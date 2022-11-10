import os
import logging
from django.db import transaction

from evm_contracts_db.settings import BASE_DIR
from evm_contracts_db.database.models import blockchain
from evm_contracts_db.database.etl.trueblocks_extractor import TrueblocksExtractor
from evm_contracts_db.database.etl.trueblocks_transformer import TrueblocksTransformer
from evm_contracts_db.database.etl.trueblocks_loader import TrueblocksLoader

from utils.files import load_json, save_json


class TrueblocksHandler:
    """Run chifra commands and extract, transform, and load the outputs of these
    e.g., `chifra traces --articulate --fmt json [addresses]` 
    """

    def __init__(self, chain=None, saveDir=None):
        self.extractor = TrueblocksExtractor()
        self.transformer = TrueblocksTransformer()
        self.loader = TrueblocksLoader(chain=chain)

        if saveDir is None:
            self.saveDir = BASE_DIR
        else:
            self.saveDir = saveDir

    def add_or_update_address_traces(self, addressObj, debug=False, reuseList=False):
        """Get list of all transaction ids from index, then export trace 

        If debug=True, saves result to file in tmp directory
        """

        address = addressObj.address

        fpath = os.path.join(self.saveDir, f"tmp/trueblocks_traces_{address}.json")

        if not os.path.isfile(fpath) or not reuseList:
            # Get list of all transaction IDs
            txIds = self.extractor.get_txids(address)

            # Filter transaction IDs for those not yet in database
            existingTxIds = blockchain.BlockchainTransaction.objects.filter(transaction_id__in=txIds).values_list('transaction_id', flat=True)
            newTxIds = list(filter(lambda id: id not in existingTxIds, txIds))
            logging.info(f"Processing {len(newTxIds)} transactions (of {len(txIds)} total transactions found)")

            # Get all transaction traces
            logging.info("Running chifra traces for the list of tx ids...")
            query_trace = {
                'function': 'traces', 
                'value': newTxIds, 
                'format': 'json',
                'args': ['articulate']
            }  
            
            cmd = self.extractor.build_chifra_command(query_trace)
            result = self.extractor.run_chifra(cmd, parse_as='json', fpath=fpath)
        else:
            logging.info(f"Using existing trace list from file for {address}")
            result = load_json(fpath)
        
        parsed = self.transformer.transform_chifra_trace_result(result)
        
        if debug:
            fpath_parsed = os.path.join(self.saveDir, f"tmp/trueblocks_{address}_parsed.json")
            save_json(parsed, fpath_parsed)

        logging.info(f"Adding {len(parsed)} transactions to database...")
        self.insert_transactions(parsed)    

    def add_or_update_address_transactions(self, addressObj, since_block=False, local_only=False):
        """Get list of all transaction ids from index, then export logs
        
        since_block options: 
            - None: look for most recent appearance of block in [int block_number|False]

        TODO: Test!!
        """

        address = addressObj.address

        fpath = os.path.join(os.getcwd(), f"tmp/trueblocks_txns_{address}.json")
        fpath_parsed = os.path.join(os.getcwd(), f"tmp/trueblocks_{address}_parsed.json")

        if not os.path.isfile(fpath):
            # Get list of all transaction IDs
            txIds = self.extractor.get_txids(address)

            # Filter transaction IDs for those since most recent appearance in chain
            if since_block is not False:
                #if since_block is None:
                #    since_block = addressObj.most_recent_appearance() # TODO: add support for this
                #else:
                since_block = str(since_block)

                txIds = list(filter(lambda id: int(id.split('.')[0]) > since_block, txIds))

            # Get all transaction traces
            logging.info("Running chifra transactions for the list of tx ids...")
            query_txn = {
                'function': 'transactions', 
                'value': txIds, 
                'format': 'json',
                'args': ['articulate']
            }  
            
            cmd = self.extractor.build_chifra_command(query_txn)
            result = self.extractor.run_chifra(cmd, parse_as='json', fpath=fpath)
        else:
            result = load_json(fpath)
        
        parsed = self.transformer.transform_chifra_transaction_result(result)
        
        if local_only:
            save_json(parsed, fpath_parsed)
        if not local_only:
            # Insert transactions
            logging.info(f"Adding {len(parsed)} transactions to database...")
            self.insert_transactions(parsed)    

    def insert_transactions(self, dataDicts, includeTraces=False):
        """Upload all blockchain transactions in file"""

        with transaction.atomic():
            for d in dataDicts:
                logging.debug(f"Updating/creating BlockchainTransaction for {d['transaction_id']}...")
                self.loader.update_or_create_transaction_record(d, includeTraces)

        logging.info(f'Added {len(dataDicts)} transactions to database')
