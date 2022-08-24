from django.db import models
from django.db.models import Q

from utils.blockchain import get_timestamp, unpack_compressed_call


class BlockchainAddress(models.Model):
    class Chains(models.TextChoices):
        MAINNET = 'ETH', 'Ethereum',
        RINKEBY = 'RIN', 'Rinkeby',
        ROPSTEn = 'ROP', 'Ropsten',
        GOERLI = 'GOE', 'GOERLI',
        KOVAN = 'KOV', 'Kovan',
        GNOSIS = 'GNO', 'Gnosis',
        OPTIMISM = 'OPT', 'Optimism',
        POLYGON = 'POL', 'Polygon'

    chain = models.CharField(
        max_length=3, 
        choices=Chains.choices, 
        default=Chains.MAINNET
    )
    address = models.CharField(max_length=42, null=False)

    def appears_in(self):
        """ Return QuerySet of all transactions in which the address appears
        Uses related_names defined in BlockchainTransaction

        This has not been tested and probably misses something... use with caution!!
        """

        txns = self.transactions_from.all()
        txns = txns.union(self.transactions_to.all())
        txns = txns.union(self.created_by_transaction.all())
        txns = txns.union(self.transactions_involving.all())

        return txns

    def save(self, *args, **kwargs):
        """Overwrite save method to ensure address is lowercase"""

        self.address = self.address.lower()
        super(BlockchainAddress, self).save(*args, **kwargs)

    class Meta:
        db_table = "blockchain_addresses"

        # Uniqueness constraint on chain-address pairs
        constraints = [
            models.UniqueConstraint(fields=['chain', 'address'], name='unique_address')
        ]

    def __str__(self):
        return self.address


class BlockchainTransaction(models.Model):
    transaction_id = models.CharField(primary_key=True, max_length=20, default="0.0")
    transaction_hash = models.CharField(max_length=66, null=True)
    block_number = models.PositiveIntegerField()
    from_address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.CASCADE, 
        null=True,
        related_name="transactions_from"
    )
    to_address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.CASCADE, 
        null=True,
        related_name="transactions_to"
    )
    value = models.FloatField()
    error = models.CharField(max_length=20, null=True)
    call_name = models.CharField(max_length=200, null=True)
    call_inputs = models.JSONField(default=dict, null=True)
    call_outputs = models.JSONField(default=dict, null=True)
    contracts_created = models.ManyToManyField(
        BlockchainAddress,
        related_name='created_by_transaction'
    )

    @property
    def timestamp(self):
        return get_timestamp(self.block_number)

    def contains_address(self, address):
        """Check if an address (string) appears anywhere in the transaction"""

        addressFound = (
            self.to_address.address == address or
            self.from_address.address == address or
            address in [c.address for c in self.contracts_created]
        )

        return addressFound

    class Meta:
        db_table = "blockchain_transactions"

    def __str__(self):
        return self.transaction_id


class BlockchainTransactionLog(models.Model):
    log_index = models.CharField(max_length=50, default="0.0.0") # transactionId.logIndex
    address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.CASCADE, 
        null=True,
        related_name="logs_from"
    )
    topics = models.CharField(max_length=267, null=True) # up to 4 space-separated 32-bit words
    event = models.CharField(max_length=200, null=True)
    compressed_log = models.TextField(null=True)
    originating_from = models.ForeignKey(
        BlockchainTransaction, 
        on_delete=models.CASCADE,
        null=True,
        related_name="logs"
    )

    @property
    def log_dict(self):
        return unpack_compressed_call(self.compressed_log) if self.compressed_log is not None else {}

    class Meta:
        db_table = "blockchain_logs"


class BlockchainTransactionTrace(models.Model):
    trace_address = models.CharField(max_length=50, default="0.0.0") # transactionId.traceAddress
    from_address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.CASCADE, 
        null=True,
        related_name="traces_from"
    )
    to_address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.CASCADE, 
        null=True,
        related_name="traces_to"
    )
    value = models.FloatField()
    compressed_trace = models.TextField(max_length=1000, null=True) # TODO: is there a max? Should we really be storing this?
    error = models.CharField(max_length=20, null=True)
    outputs = models.JSONField(default=dict, null=True)
    delegate = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.CASCADE,
        null=True,
        related_name="delegate_for_trace"
    )
    originating_from = models.ForeignKey(
        BlockchainTransaction, 
        on_delete=models.CASCADE,
        null=True,
        related_name="traces"
    )

    @property
    def trace_dict(self):
        return unpack_compressed_call(self.compressed_trace) if self.compressed_trace is not None else {}

    class Meta:
        db_table = "blockchain_traces"

