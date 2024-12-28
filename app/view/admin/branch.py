from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from app.models import Branch


@login_required
def branch_list(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        branches = Branch.objects.filter(
            Q(name__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    else:
        branches = Branch.objects.all()
    
    paginator = Paginator(branches, 10)
    page = request.GET.get('page')
    branches = paginator.get_page(page)
    
    context = {
        'active': 'branches',
        'branches': branches,
        'search_query': search_query
    }
    return render(request, 'admin/branch_list.html', context)

@login_required
def branch_detail(request, branch_id):
    action = request.GET.get('action', 'view')
    
    if branch_id == 0:
        branch = None
    else:
        branch = get_object_or_404(Branch, pk=branch_id)
    
    if request.method == 'POST':
        if action == 'delete':
            branch.delete()
            messages.success(request, 'Branch deleted successfully')
            return redirect('branch_list')
            
        elif action in ['edit', 'add']:
            name = request.POST.get('name')
            address = request.POST.get('address')
            city = request.POST.get('city')
            status = request.POST.get('status')
            
            if action == 'add':
                branch = Branch.objects.create(
                    name=name,
                    address=address,
                    city=city,
                    status=status
                )
                messages.success(request, 'Branch added successfully')
            else:
                branch.name = name
                branch.address = address
                branch.city = city
                branch.status = status
                branch.save()
                messages.success(request, 'Branch updated successfully')
            
            return redirect('branch_list')
    
    context = {
        'branch': branch,
        'action': action
    }
    return render(request, 'admin/branch_list.html', context)