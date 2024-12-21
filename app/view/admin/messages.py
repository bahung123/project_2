from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.models import Message, AuthUser 
from django.http import JsonResponse
from django.utils.timezone import now, localtime
from django.db import models

@login_required
def messenger(request):
    try:
        admin = AuthUser.objects.filter(is_staff=1).first()
        print(f"Current user: {request.user.id}, Admin: {admin.id}")
        
        if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            content = request.POST.get("message")
            print(f"Received message: {content}")
            
            # Determine sender and receiver
            if request.user.is_staff:
                sender_id = request.user.id  # Admin sending
                receiver_id = request.POST.get('receiver_id', None)  
                if not receiver_id:
                    # If no specific receiver, get latest conversation
                    latest_msg = Message.objects.filter(
                        models.Q(sender_id=admin.id) | 
                        models.Q(receiver_id=admin.id)
                    ).latest('timestamp')
                    receiver_id = latest_msg.sender_id if latest_msg.receiver_id == admin.id else latest_msg.receiver_id
            else:
                sender_id = request.user.id
                receiver_id = admin.id

            print(f"Sending message: sender={sender_id}, receiver={receiver_id}")
            
            message = Message.objects.create(
                sender_id=sender_id,
                receiver_id=receiver_id,
                text=content,
                timestamp=now(),
                is_read=0
            )
            
            return JsonResponse({
                'status': 'success',
                'message': {
                    'id': message.id,
                    'content': message.text,
                    'timestamp': localtime(message.timestamp).strftime("%I:%M %p"),
                    'sender_id': sender_id,
                    'receiver_id': receiver_id
                }
            })

        # Get chat history
        if request.user.is_staff:
            messages = Message.objects.all().order_by('timestamp')
        else:
            messages = Message.objects.filter(
                (models.Q(sender_id=request.user.id) & models.Q(receiver_id=admin.id)) |
                (models.Q(sender_id=admin.id) & models.Q(receiver_id=request.user.id))
            ).order_by('timestamp')

        context = {
            "messages": messages,
            "user": request.user,
            "admin": admin,
            "is_admin": request.user.is_staff
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            messages_data = [{
                'id': msg.id,
                'text': msg.text,
                'timestamp': localtime(msg.timestamp).strftime("%I:%M %p"),
                'sender_id': msg.sender_id,
                'receiver_id': msg.receiver_id
            } for msg in messages]
            return JsonResponse({'messages': messages_data})

        return render(request, "admin/messages.html", context)

    except Exception as e:
        print(f"Messenger Error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})
