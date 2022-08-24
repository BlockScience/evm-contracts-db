from evm_contracts_db.database.etl.trueblocks_extractor import TrueblocksExtractor
from evm_contracts_db.database.etl.trueblocks_transformer import TrueblocksTransformer
from evm_contracts_db.database.etl.trueblocks import TrueblocksHandler
from evm_contracts_db.database.models.blockchain import BlockchainAddress


def test_save_chifra_trace_result():
    tbe = TrueblocksExtractor()
    tbt = TrueblocksTransformer()
    tb = TrueblocksHandler()

    testQuery_list = {
        'function': 'list', 
        'value': '0x7378ad1ba8f3c8e64bbb2a04473edd35846360f1', 
        'postprocess': "| cut -f2,3 | tr '\t' '.' | grep -v blockNumber"
    }
    cmd = tbe.build_chifra_command(testQuery_list)
    txIds = tbe.run_chifra(cmd, parse_as='lines')
    testQuery_trace = {
        'function': 'traces', 
        'value': txIds, 
        'format': 'json',
        'args': ['articulate']
    }    
    cmd = tbe.build_chifra_command(testQuery_trace)
    result = tbe.run_chifra(cmd, parse_as='json')
    assert result is not None, "No result returned; error encountered"
    assert isinstance(result, dict), f"Expected list, not {type(result)}"
    
    parsed = tbt.transform_chifra_trace_result(result, factory=testQuery_list['value'])
    assert len(parsed) == len(txIds), "Did not get traces of all transactions"

    tb.insert_transactions(parsed)    
    print("Passed test save_chifra_trace_result")


def test_add_or_update_address_traces():
    # Test w/Aragon v0.6 address (has factory object attached)
    tb = TrueblocksHandler()
    addressObj = BlockchainAddress.objects.get(pk='0x595b34c93aa2c2ba0a38daeede629a0dfbdcc559')
    tb.add_or_update_address_traces(addressObj)


def test_add_or_update_address_transactions():
    # Test w/some random Aragon AppProxyUpgradeable address
    dao_address = '0xe9d7e590171cb5080ab8dfd45850692a714260f0' #defi omega
    addressObj = BlockchainAddress.objects.get(pk=dao_address)

    tb = TrueblocksHandler()
    tb.add_or_update_address_transactions(addressObj)   


if __name__ == "__main__":
    test_save_chifra_trace_result()
    test_add_or_update_address_traces()
    test_add_or_update_address_transactions()
    