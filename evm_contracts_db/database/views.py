import os
from django.shortcuts import render

from evm_contracts_db.database.models import BlockchainAddress, BlockchainTransaction


def index(request):
    """View function for home page of site"""

    # Generate counts of some of the main objects
    stats = {
        'addressCount': BlockchainAddress.objects.all().count(),
        'txCount': BlockchainTransaction.objects.all().count()
    }
    context = {
        'stats': stats,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)
