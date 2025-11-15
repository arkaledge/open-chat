"""Branch and threading API endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.base import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.schemas.branch import (
    BranchCreate,
    BranchInfo,
    BranchTree,
    ThreadMessage,
    MessageBranchRequest,
    RegenerateMessageRequest,
    MessageEdit
)
from app.schemas.conversation import ConversationResponse
from app.utils.dependencies import get_current_user
from app.services.llm_service import LLMService


router = APIRouter(prefix="/branches", tags=["Branches & Threading"])
llm_service = LLMService()


@router.post("/conversations/{conversation_id}/branch", response_model=ConversationResponse)
async def branch_conversation(
    conversation_id: str,
    branch_data: BranchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation branch from an existing conversation.

    This creates a complete copy of the conversation up to the current point,
    allowing you to explore alternative conversation paths.
    """

    # Get original conversation
    original_conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not original_conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Create new branched conversation
    new_conv = Conversation(
        user_id=current_user.id,
        workspace_id=original_conv.workspace_id,
        title=branch_data.title or f"Branch: {original_conv.title}",
        model=original_conv.model,
        parent_conversation_id=original_conv.id,
        metadata={
            **original_conv.metadata,
            "branched_from": str(conversation_id),
            "branch_type": "conversation"
        }
    )
    db.add(new_conv)
    db.flush()

    # Copy all messages
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()

    for msg in messages:
        new_msg = Message(
            conversation_id=new_conv.id,
            role=msg.role,
            content=msg.content,
            model=msg.model,
            metadata=msg.metadata
        )
        db.add(new_msg)

    # Update branch count on parent
    original_conv.branch_count += 1

    db.commit()
    db.refresh(new_conv)

    return new_conv


@router.post(
    "/conversations/{conversation_id}/messages/{message_id}/branch",
    response_model=ConversationResponse
)
async def branch_from_message(
    conversation_id: str,
    message_id: str,
    branch_request: MessageBranchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation branch starting from a specific message.

    This allows you to explore "what if" scenarios by branching at any point
    in the conversation and taking it in a different direction.
    """

    # Get original conversation and message
    original_conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not original_conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    branch_message = db.query(Message).filter(
        Message.id == message_id,
        Message.conversation_id == conversation_id
    ).first()

    if not branch_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Create new branched conversation
    new_conv = Conversation(
        user_id=current_user.id,
        workspace_id=original_conv.workspace_id,
        title=f"Branch from: {branch_message.content[:30]}...",
        model=branch_request.model or original_conv.model,
        parent_conversation_id=original_conv.id,
        branched_at_message_id=message_id,
        metadata={
            **original_conv.metadata,
            "branched_from": str(conversation_id),
            "branched_at_message": str(message_id),
            "branch_type": "message"
        }
    )
    db.add(new_conv)
    db.flush()

    # Copy messages up to and including the branch point
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.created_at <= branch_message.created_at
    ).order_by(Message.created_at).all()

    for msg in messages:
        new_msg = Message(
            conversation_id=new_conv.id,
            role=msg.role,
            content=branch_request.new_content if msg.id == message_id and branch_request.new_content else msg.content,
            model=msg.model,
            parent_message_id=message_id if msg.id == message_id else None,
            thread_id=message_id,
            metadata=msg.metadata
        )
        db.add(new_msg)

    # Update branch count
    original_conv.branch_count += 1

    db.commit()
    db.refresh(new_conv)

    return new_conv


@router.get("/conversations/{conversation_id}/tree", response_model=BranchTree)
async def get_branch_tree(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the complete branch tree for a conversation.

    This shows all branches and sub-branches, allowing you to navigate
    the entire conversation history tree.
    """

    def build_tree(conv_id: str, depth: int = 0) -> BranchTree:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not conv:
            return None

        # Get message count
        msg_count = db.query(func.count(Message.id)).filter(
            Message.conversation_id == conv_id
        ).scalar()

        # Get child branches
        children = db.query(Conversation).filter(
            Conversation.parent_conversation_id == conv_id
        ).all()

        return BranchTree(
            conversation_id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            message_count=msg_count,
            branches=[build_tree(str(child.id), depth + 1) for child in children]
        )

    # Verify access
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Find root conversation
    root_conv = conv
    while root_conv.parent_conversation_id:
        root_conv = db.query(Conversation).filter(
            Conversation.id == root_conv.parent_conversation_id
        ).first()

    return build_tree(str(root_conv.id))


@router.get("/conversations/{conversation_id}/branches", response_model=List[BranchInfo])
async def list_conversation_branches(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all direct branches from a conversation.
    """

    # Verify access
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Get branches
    branches = db.query(Conversation).filter(
        Conversation.parent_conversation_id == conversation_id
    ).all()

    result = []
    for branch in branches:
        # Calculate branch depth
        depth = 0
        current = branch
        while current.parent_conversation_id:
            depth += 1
            current = db.query(Conversation).filter(
                Conversation.id == current.parent_conversation_id
            ).first()
            if not current:
                break

        result.append(BranchInfo(
            conversation_id=branch.id,
            parent_conversation_id=branch.parent_conversation_id,
            branched_at_message_id=branch.branched_at_message_id,
            branch_depth=depth,
            title=branch.title,
            created_at=branch.created_at
        ))

    return result


@router.post(
    "/messages/{message_id}/regenerate",
    response_model=ConversationResponse
)
async def regenerate_message(
    message_id: str,
    regen_request: RegenerateMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Regenerate an assistant message with different parameters.

    If keep_original is True, creates a branch with the new version.
    Otherwise, replaces the existing message.
    """

    # Get message
    message = db.query(Message).filter(Message.id == message_id).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Verify conversation access
    conv = db.query(Conversation).filter(
        Conversation.id == message.conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if message.role != "assistant":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only regenerate assistant messages"
        )

    # Get context (messages before this one)
    context_messages = db.query(Message).filter(
        Message.conversation_id == message.conversation_id,
        Message.created_at < message.created_at
    ).order_by(Message.created_at).all()

    # Build message list
    messages_list = [{"role": m.role, "content": m.content} for m in context_messages]

    # Generate new response
    model = regen_request.model or message.model or conv.model
    completion = await llm_service.chat_completion(
        messages=messages_list,
        model=model,
        temperature=regen_request.temperature or 0.7,
        max_tokens=regen_request.max_tokens,
        stream=False
    )

    if regen_request.keep_original:
        # Create branch with new version
        new_conv = Conversation(
            user_id=current_user.id,
            workspace_id=conv.workspace_id,
            title=f"Regeneration: {conv.title}",
            model=model,
            parent_conversation_id=conv.id,
            branched_at_message_id=message_id,
            metadata={
                **conv.metadata,
                "branch_type": "regeneration",
                "original_message": str(message_id)
            }
        )
        db.add(new_conv)
        db.flush()

        # Copy messages up to regeneration point
        for msg in context_messages:
            new_msg = Message(
                conversation_id=new_conv.id,
                role=msg.role,
                content=msg.content,
                model=msg.model
            )
            db.add(new_msg)

        # Add regenerated message
        new_msg = Message(
            conversation_id=new_conv.id,
            role="assistant",
            content=completion["content"],
            model=model,
            parent_message_id=message_id,
            metadata={"regenerated": True}
        )
        db.add(new_msg)

        conv.branch_count += 1
        db.commit()
        db.refresh(new_conv)

        return new_conv
    else:
        # Replace existing message
        message.content = completion["content"]
        message.model = model
        message.metadata = {**message.metadata, "regenerated": True}

        db.commit()
        db.refresh(conv)

        return conv


@router.post("/messages/{message_id}/edit", response_model=ConversationResponse)
async def edit_message(
    message_id: str,
    edit_request: MessageEdit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Edit a user message and optionally regenerate the response.

    If create_branch is True, creates a new conversation branch.
    Otherwise, modifies the existing conversation.
    """

    # Get message
    message = db.query(Message).filter(Message.id == message_id).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Verify access
    conv = db.query(Conversation).filter(
        Conversation.id == message.conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if message.role != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only edit user messages"
        )

    if edit_request.create_branch:
        # Create branch with edited message
        new_conv = Conversation(
            user_id=current_user.id,
            workspace_id=conv.workspace_id,
            title=f"Edit: {conv.title}",
            model=conv.model,
            parent_conversation_id=conv.id,
            branched_at_message_id=message_id,
            metadata={
                **conv.metadata,
                "branch_type": "edit",
                "original_content": message.content
            }
        )
        db.add(new_conv)
        db.flush()

        # Copy messages up to edit point
        messages_before = db.query(Message).filter(
            Message.conversation_id == message.conversation_id,
            Message.created_at < message.created_at
        ).order_by(Message.created_at).all()

        for msg in messages_before:
            new_msg = Message(
                conversation_id=new_conv.id,
                role=msg.role,
                content=msg.content,
                model=msg.model
            )
            db.add(new_msg)

        # Add edited message
        edited_msg = Message(
            conversation_id=new_conv.id,
            role="user",
            content=edit_request.content,
            parent_message_id=message_id,
            metadata={"edited": True, "original_content": message.content}
        )
        db.add(edited_msg)

        # Regenerate response if requested
        if edit_request.regenerate_response:
            messages_list = [{"role": m.role, "content": m.content} for m in messages_before]
            messages_list.append({"role": "user", "content": edit_request.content})

            completion = await llm_service.chat_completion(
                messages=messages_list,
                model=conv.model,
                stream=False
            )

            response_msg = Message(
                conversation_id=new_conv.id,
                role="assistant",
                content=completion["content"],
                model=conv.model
            )
            db.add(response_msg)

        conv.branch_count += 1
        db.commit()
        db.refresh(new_conv)

        return new_conv
    else:
        # Edit in place
        message.content = edit_request.content
        message.metadata = {**message.metadata, "edited": True}

        db.commit()
        db.refresh(conv)

        return conv
