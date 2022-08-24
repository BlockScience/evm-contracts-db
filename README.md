# evm_contracts_db

**evm_contracts_db** is a Django framework and set of ETL modules for setting up a Postgres database to store Solidity smart contract and transaction data from EVM-compatible chains using [TrueBlocks](https://trueblocks.io/).

## Install

### Basic install
1. Create a Python environment from `requirements.txt`. If you are using `pip`, make sure Python 3.9 is installed. If you are using `conda`, run the following commands:
```
conda create -n evm-db python=3.9
conda activate evm-db
pip install -r requirements.txt
```
2. Create a new Postgres database. 
3. Create a .env file in the root directory with the credentials required to access the database:
```
DATABASE=
DB_HOSTNAME=
DB_PORT=
DB_USERNAME=
DB_PASSWORD=
```

### TrueBlocks install
Install TrueBlocks according to [the current instructions](https://trueblocks.io/). 
We recommend adding both Go and TrueBlocks to `PATH` by adding the following line at the end of `~/.profile`:
`export PATH=$PATH:/usr/local/go/bin:$HOME/trueblocks-core/bin`. If you want to use the index built by TrueBlocks, run `chifra init --all`; if instead you are running your own node, run `chifra scrape`. 
