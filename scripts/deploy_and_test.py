import json
from web3 import Web3
from solcx import compile_source, set_solc_version

# 设置 solc 版本
set_solc_version("0.8.19")

# 1. 连接 Ganache
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
assert w3.is_connected(), "无法连接 Ganache"
print(f"✓ 已连接 Ganache (chain ID: {w3.eth.chain_id})")

# 2. 使用 Ganache 第一个账户（私钥已知）
account = w3.eth.accounts[0]
private_key = "0x7e137a11056fa99ae145fb20d5692334b1ea0577dec291ce0f4553e3fd00bf78"
print(f"✓ 使用账户: {account}")
print(f"  余额: {w3.from_wei(w3.eth.get_balance(account), 'ether')} ETH")

# 3. 编译合约
contract_path = "contracts/EnergyData.sol"
with open(contract_path) as f:
    source = f.read()

compiled = compile_source(source, output_values=["abi", "bin"])
contract_interface = compiled["<stdin>:EnergyData"]

print(f"✓ 合约编译成功")
print(f"  Bytecode 长度: {len(contract_interface['bin'])} bytes")

# 4. 部署合约
contract = w3.eth.contract(abi=contract_interface["abi"], bytecode=contract_interface["bin"])

tx = contract.constructor().build_transaction({
    "from": account,
    "nonce": w3.eth.get_transaction_count(account),
    "gas": 3000000,
    "gasPrice": w3.eth.gas_price,
})

signed = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"✓ 合约部署成功")
print(f"  交易哈希: {tx_hash.hex()}")
print(f"  合约地址: {receipt.contractAddress}")
print(f"  Gas 消耗: {receipt.gasUsed}")

# 5. 调用 storeHash 写入数据
contract_instance = w3.eth.contract(
    address=receipt.contractAddress,
    abi=contract_interface["abi"],
)

test_hash = "QmYwAPJzv5CZsnAzt8auVZRnA3XwPqH5BPfU3PmHVMBL6r"

tx = contract_instance.functions.storeHash(test_hash).build_transaction({
    "from": account,
    "nonce": w3.eth.get_transaction_count(account),
    "gas": 300000,
    "gasPrice": w3.eth.gas_price,
})

signed = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"\n✓ storeHash 写入成功")
print(f"  交易哈希: {tx_hash.hex()}")
print(f"  写入哈希: {test_hash}")

# 6. 调用 getHash 读取验证
result = contract_instance.functions.getHash().call()
print(f"\n✓ getHash 读取成功")
print(f"  链上存储的哈希: {result}")
print(f"  写入与读取一致: {result == test_hash}")
