from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from app.models import Bill
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.http import HttpResponse
from django.utils.text import slugify
from reportlab.lib.colors import black, grey, lightgrey, darkblue, white
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import Paragraph
from reportlab.lib.colors import HexColor
import qrcode
from io import BytesIO

# Add QR code import with try-except
try:
    import qrcode
    QR_ENABLED = True
except ImportError:
    print("QR code functionality disabled - missing qrcode package")
    QR_ENABLED = False

@login_required
def bill_list(request):
    try:
        # Get search and filter parameters
        search_query = request.GET.get('search', '').strip()
        paid_status = request.GET.get('paid_status', '').strip()

        # Base queryset with newest bills first
        bills = Bill.objects.all().order_by('-date_issued', '-id')

        # Apply search filter
        if search_query:
            bills = bills.filter(
                Q(reservation__guest__full_name__icontains=search_query) |
                Q(reservation__guest__email__icontains=search_query) |
                Q(reservation__guest__phone_number__icontains=search_query)
            ).distinct()

        # Apply status filter
        if paid_status:
            bills = bills.filter(paid_status=paid_status)

        # Pagination
        page_size = 10
        paginator = Paginator(bills, page_size)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context = {
            'bills': page_obj,
            'page_obj': page_obj,
            'search_query': search_query,
            'paid_status': paid_status,
            'active': 'bills',
            'total_bills': Bill.objects.count(),
            'filtered_count': bills.count(),
            'title': 'Bill List'
        }

        return render(request, 'admin/bill_list.html', context)

    except Exception as e:
        messages.error(request, f'Error loading bills: {str(e)}')
        return render(request, 'admin/bill_list.html', {'active': 'bills'})

@login_required
def bill_edit(request, bill_id):
    try:
        bill = get_object_or_404(Bill, id=bill_id)
        if request.method == 'POST':
            # Update bill details
            bill.paid_status = request.POST.get('paid_status')
            bill.save()            
            messages.success(request, 'Bill updated successfully.')
            
    except Exception as e:
        print(f"Debug - Error in bill_edit: {str(e)}")  # Debug log
        messages.error(request, f'Error updating bill: {str(e)}')
    
    return redirect('bill_list')

@login_required
def bill_delete(request, bill_id):
    try:
        if request.method == 'POST':
            bill = get_object_or_404(Bill, id=bill_id)
            bill.delete()
            messages.success(request, 'Bill deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting bill: {str(e)}')
    
    return redirect('bill_list')


@login_required
def export_bill_pdf(request, bill_id):
    try:
        bill = get_object_or_404(Bill, id=bill_id)
        width, height = A4
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="luxury_invoice_{bill.id}.pdf"'
        p = canvas.Canvas(response, pagesize=A4)

        # Elegant header with gradient
        p.setFillColor(HexColor('#0A1747'))  # Deep navy
        p.rect(0, height-200, width, 200, fill=True)
        
        # Gold accent line
        p.setStrokeColor(HexColor('#C5A572'))  # Gold
        p.setLineWidth(3)
        p.line(40, height-210, width-40, height-210)

        # Hotel logo/name
        p.setFillColor(HexColor('#C5A572'))
        p.setFont("Helvetica-Bold", 40)
        p.drawString(50, height-80, "LUXURY")
        p.setFillColor(white)
        p.drawString(220, height-80, "HOTEL")
        
        # Contact info in gold
        p.setFont("Helvetica", 12)
        p.setFillColor(HexColor('#C5A572'))
        p.drawString(50, height-110, "123 Paradise Avenue • Luxury City • +1 234 567 890")

        # Invoice details box
        p.setFillColor(HexColor('#F8F9FA'))
        p.roundRect(40, height-320, width-80, 80, 10, fill=True)
        p.setFillColor(HexColor('#0A1747'))
        p.setFont("Helvetica-Bold", 16)
        p.drawString(60, height-260, f"Invoice #{bill.id}")
        p.setFont("Helvetica", 12)
        p.drawString(60, height-280, f"Date: {bill.date_issued.strftime('%B %d, %Y')}")
        p.drawString(60, height-300, f"Status: {bill.paid_status.upper()}")

        # Guest details with elegant box
        p.setFillColor(HexColor('#F8F9FA'))
        p.roundRect(40, height-450, width-80, 100, 10, fill=True)
        p.setFillColor(HexColor('#0A1747'))
        p.setFont("Helvetica-Bold", 14)
        p.drawString(60, height-390, "Guest Details")
        p.setFont("Helvetica", 12)
        p.drawString(60, height-410, f"Guest: {bill.reservation.guest.full_name}")
        p.drawString(60, height-430, f"Email: {bill.reservation.guest.email}")
        
        # Reservation details
        p.drawString(350, height-410, f"Check-in: {bill.reservation.check_in_date.strftime('%b %d, %Y')}")
        p.drawString(350, height-430, f"Check-out: {bill.reservation.check_out_date.strftime('%b %d, %Y')}")

        # Charges table with alternating colors
        y = height-500
        headers = ["Description", "Amount"]
        
        # Table header
        p.setFillColor(HexColor('#0A1747'))
        p.roundRect(40, y, width-80, 30, 5, fill=True)
        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(60, y+10, headers[0])
        p.drawString(width-160, y+10, headers[1])

        # Table content
        items = [
            ("Room Charges", bill.total_amount - bill.early_checkin_fee - bill.late_checkout_fee),
            ("Early Check-in Fee", bill.early_checkin_fee),
            ("Late Check-out Fee", bill.late_checkout_fee)
        ]

        for i, (desc, amount) in enumerate(items):
            y -= 30
            # Alternating row colors
            if i % 2 == 0:
                p.setFillColor(HexColor('#F8F9FA'))
                p.rect(40, y, width-80, 25, fill=True)
            p.setFillColor(HexColor('#0A1747'))
            p.setFont("Helvetica", 12)
            p.drawString(60, y+7, desc)
            p.drawRightString(width-60, y+7, f"${amount:.2f}")

        # Total with gold accent
        y -= 50
        p.setFillColor(HexColor('#0A1747'))
        p.setLineWidth(2)
        p.line(40, y+30, width-40, y+30)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(60, y, "Total Amount:")
        p.setFillColor(HexColor('#C5A572'))
        p.drawRightString(width-60, y, f"${bill.total_amount:.2f}")

        # deposit amount
        y -= 30
        p.setFont("Helvetica", 12)
        p.setFillColor(HexColor('#0A1747'))
        p.drawString(60, y, "Deposit Amount:")
        p.setFillColor(HexColor('#C5A572'))
        p.drawRightString(width-60, y, f"${bill.deposit_amount:.2f}")

        #Payment required
        y -= 30
        p.setFont("Helvetica-Bold", 12)
        p.setFillColor(HexColor('#0A1747'))
        p.drawString(60, y, "Payment Required:")
        p.setFillColor(HexColor('#C5A572'))
        p.drawRightString(width-60, y, f"${bill.total_amount-bill.deposit_amount:.2f}")

        # Footer with QR and thank you note
        p.setFillColor(HexColor('#0A1747'))
        p.setFont("Helvetica", 12)  # Changed from Helvetica-Italic
        p.drawCentredString(width/2, 80, "Thank you for choosing Luxury Hotel")
        p.drawCentredString(width/2, 60, "We look forward to serving you again")

        # QR Code in bottom left with RGB color tuple
        if QR_ENABLED:
            qr = qrcode.QRCode(version=1, box_size=2)
            qr.add_data(f"Invoice #{bill.id} - Total: ${bill.total_amount:.2f}")
            qr.make()
            # Use RGB tuple (10, 23, 71) instead of HexColor
            img = qr.make_image(fill_color=(10, 23, 71), back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            p.drawImage(ImageReader(BytesIO(buffer.getvalue())), 40, 40, width=70, height=70)

        p.showPage()
        p.save()
        return response

    except Exception as e:
        print(f"PDF Generation Error: {str(e)}")
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('bill_list')