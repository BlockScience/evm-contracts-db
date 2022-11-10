import logging
from django.db import transaction

from evm_contracts_db.database.models import blockchain


class TrueblocksLoader:
    """Load the output of TrueblocksTransformer into the database"""

    def __init__(self, chain=None):
        """By default, assume addresses are on Ethereum mainnet"""
        if chain is None:
            self.chain = 'ETH'
        else:
            self.chain = chain

    def insert_transactions(self, dataDicts, includeTraces=False):
        """Upload all blockchain transactions in file"""

        with transaction.atomic():
            for d in dataDicts:
                logging.debug(f"Updating/creating BlockchainTransaction for {d['transaction_id']}...")
                self.update_or_create_transaction_record(d, includeTraces)

        logging.info(f'Added {len(dataDicts)} transactions to database')

    def update_or_create_address_record(self, address):
        try:
            addressObj = blockchain.BlockchainAddress.objects.get(address=address, chain=self.chain)
        except blockchain.BlockchainAddress.DoesNotExist:
            addressObj = blockchain.BlockchainAddress.objects.create(address=address, chain=self.chain)
            addressObj.save()

        return addressObj

    def update_or_create_trace_record(self, traceDict):
        for addressType in ['from_address', 'to_address', 'delegate']:
            value = traceDict.get(addressType)
            if value is not None:
                traceDict[addressType] = self.update_or_create_address_record(value)
        traceObj = blockchain.BlockchainTransactionTrace.objects.update_or_create(**traceDict)[0]
        traceObj.save()

        return traceObj

    def update_or_create_log_record(self, logDict):
        value = logDict.get('address', '0x0')
        logDict['address'] = self.update_or_create_address_record(value)
        logObj = blockchain.BlockchainTransactionLog.objects.update_or_create(**logDict)[0]
        logObj.save()

        return logObj

    def update_or_create_transaction_record(self, recordDict, only_create=False, includeTraces=False):
        """Create new transaction from dictionary of model parameters"""

        if recordDict is None or recordDict == {}:
            return
        
        # Create BlockchainAddress record for from and to addresses if they doesn't already exist
        for addressType in ['from_address', 'to_address']:
            value = recordDict.get(addressType, '0x0')
            recordDict[addressType] = self.update_or_create_address_record(value)

        # Create BlockchainAddress record for each created contract, if any
        contractsCreated_orig = recordDict.pop('contracts_created', [])
        contractsCreated = []
        for c in contractsCreated_orig:
            contractsCreated.append(self.update_or_create_address_record(c))

        # Create BlockchainAddress record for each involved address, if any
        # TODO: find a way to more reliably get all addresses involved. Curently
        # this is not included in the data model because it was too incomplete.
        addressesInvolved_orig = recordDict.pop('addresses_involved', [])
        addressesInvolved = []
        for c in addressesInvolved_orig:
            if (c not in contractsCreated) and not (
                c == recordDict.get('from_address') or c == recordDict.get('from_address')
            ):
                addressesInvolved.append(self.update_or_create_address_record(c))

        # Create log record for each log, if any
        logs_orig = recordDict.pop('logs', [])
        logs = []
        for l in logs_orig:
            logs.append(self.update_or_create_log_record(l))

        # Create trace record for each trace, if any
        if includeTraces:
            traces_orig = recordDict.pop('traces', [])
            traces = []
            for t in traces_orig:
                traces.append(self.update_or_create_trace_record(t))
        else:
            recordDict.pop('traces', None)

        # Update or create BlockchainTransaction record
        try:
            txn = blockchain.BlockchainTransaction.objects.get(transaction_id=recordDict['transaction_id'])
            for key, value in recordDict.items():
                if key not in ['contracts_created', 'logs', 'traces']:
                    setattr(txn, key, value)
                else:
                    if key == 'contracts_created':
                        txn.contracts_created.add(*value)
                    # if key == 'addresses_involved':
                    #     txn.addresses_involved.add(*value)
                    if key == 'logs':
                        txn.logs.add(*value)
                    if key == 'traces':
                        txn.traces.add(*value)
            txn.save()
            logging.debug(f"Updated transaction already in database")
        except blockchain.BlockchainTransaction.DoesNotExist:
            txn = blockchain.BlockchainTransaction.objects.create(**recordDict)
            txn.save()
            txn.contracts_created.set(contractsCreated)
            # txn.addresses_involved.set(addressesInvolved)
            txn.logs.set(logs)
            if includeTraces:
                txn.traces.set(traces)
            logging.debug("Added new transaction to database...")

        return txn