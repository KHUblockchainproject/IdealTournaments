## 블록체인을 활용한 이상형 월드컵 - Server part

### Installation & Quick Start
```shell
git clone https://github.com/KHUblockchainproject/IdealTournaments.git
cd IdealTournaments/

python -m pip install -r vote_part/requirements.txt

vim .env
```

```shell
# .env File
ETHEREUM_NODE_URL=https://public-en-kairos.node.kaia.io/
ADMIN_ADDRESS=<관리자 지갑주소>
PRIVATE_KEY=<관리자 Private Key>
SOLC_VERSION=0.8.26
```

<br>

- Execution
```py
python blockchain_project/app.py
python vote_part/vote.py
```