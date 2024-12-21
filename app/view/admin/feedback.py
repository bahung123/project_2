from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from app.models import Feedback
from django.contrib import messages

@login_required
def feedback_list(request):
    try:
        # Check if user is staff
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('index')

        # Get search query
        search = request.GET.get('search', '')
        rating = request.GET.get('rating', '')
        sort = request.GET.get('sort', 'newest')

        # Base query
        feedbacks = Feedback.objects.select_related('guest', 'reservation')

        # Apply search
        if search:
            feedbacks = feedbacks.filter(
                Q(guest__full_name__icontains=search) |
                Q(comment__icontains=search)
            )

        # Apply rating filter
        if rating:
            feedbacks = feedbacks.filter(rating=rating)

        # Apply sorting
        if sort == 'oldest':
            feedbacks = feedbacks.order_by('created_at')
        elif sort == 'rating':
            feedbacks = feedbacks.order_by('-rating', '-created_at')
        else:  # newest
            feedbacks = feedbacks.order_by('-created_at')

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(feedbacks, 10)
        feedbacks = paginator.get_page(page)

        context = {
            'feedbacks': feedbacks,
            'search': search,
            'rating': rating,
            'sort': sort,
            'active': 'feedback'  # For sidebar active state
        }

        return render(request, 'admin/feedback_list.html', context)

    except Exception as e:
        print(f"Feedback list error: {str(e)}")
        messages.error(request, "Error loading feedback list")
        return redirect('base_admin')  # Changed from admin_dashboard to base_admin