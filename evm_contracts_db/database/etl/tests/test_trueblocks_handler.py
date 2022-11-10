from evm_contracts_db.database.etl.trueblocks import TrueblocksHandler
from evm_contracts_db.database.models.blockchain import BlockchainAddress


def test_add_or_update_address_traces():
    # Test w/Aragon v0.6 address
    tb = TrueblocksHandler()
    factory_address = '0x595b34c93aa2c2ba0a38daeede629a0dfbdcc559'
    addressObj = tb.loader.update_or_create_address_record(address=factory_address)
    tb.add_or_update_address_traces(addressObj)


def test_add_or_update_address_transactions():
    # Test w/some random Aragon AppProxyUpgradeable address
    tb = TrueblocksHandler()
    dao_address = '0xe9d7e590171cb5080ab8dfd45850692a714260f0' #defi omega
    addressObj = tb.loader.update_or_create_address_record(address=dao_address)
    tb.add_or_update_address_transactions(addressObj)   
