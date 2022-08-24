from django.db import models

from evm_contracts_db.database.models.blockchain import BlockchainAddress


class AddressOwner(models.Model):
    """This table is intended to store metadata about owners of one or more 
    blockchain_addresses (e.g., a DAO).
    """

    name = models.CharField(max_length=200, null=False)
    website = models.URLField(max_length=200, null=True)
    blockchain_addresses = models.ManyToManyField(
        BlockchainAddress,
        related_name='belongs_to_owner'
    )

    class Meta:
        db_table = "address_owners"

    def __str__(self):
        return self.name
