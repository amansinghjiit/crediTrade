from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CreditCard
from .forms import CreditCardForm
from django.contrib import messages

@login_required
def my_cards(request):
    cards = CreditCard.objects.filter(user=request.user)
    banks = cards.values_list('bank', flat=True).distinct()
    form = CreditCardForm()
    return render(request, 'cards/my_cards.html', {
        'cards': cards,
        'banks': banks,
        'form': form
    })

@login_required
def add_card(request):
    if request.method == 'POST':
        form = CreditCardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.user = request.user
            card.save()
            messages.success(request, "Card added")
    return redirect('my_cards')

@login_required
def delete_card(request, card_id):
    card = get_object_or_404(CreditCard, id=card_id, user=request.user)
    card.delete()
    messages.success(request, "Card deleted")
    return redirect('my_cards')
