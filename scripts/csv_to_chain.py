import hashlib
import csv
import os
from web3 import Web3
from solcx import compile_source, set_solc_version

set_solc_version("0.8.19")

# ============================================================
# 1. 读取 CSV 能源数据
# ============================================================
csv_path = "data/energy_data.csv"
rows = []
with open(csv_path, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

print(f"✓ 读取 CSV 完成，共 {len(rows)} 条记录")
for i, row in enumerate(rows):
    print(f"  [{i+1}] {row['timestamp']} | {row['device_id']} | "
          f"生产:{row['energy_production_kwh']}kWh | 消耗:{row['energy_consumption_kwh']}kWh")

# ============================================================
# 2. 计算 SHA256 哈希
# ============================================================
# 将整个 CSV 内容（原始字节）计算 SHA256，保证数据完整性
with open(csv_path, "rb") as f:
    raw_bytes = f.read()

sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
print(f"\n✓ SHA256 哈希计算完成")
print(f"  哈希值: 0x{sha256_hash}")

# ============================================================
# 3. 连接 Ganache & 编译合约
# ============================================================
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
assert w3.is_connected(), "无法连接 Ganache"

account = w3.eth.accounts[0]
print(f"  账户: {account}")

contract_source = open("contracts/EnergyData.sol").read()
compiled = compile_source(contract_source, output_values=["abi", "bin"])
contract_interface = compiled["<stdin>:EnergyData"]

# ============================================================
# 4. 部署合约（Ganache 账户已解锁，直接 send_transaction）
# ============================================================
contract = w3.eth.contract(abi=contract_interface["abi"], bytecode=contract_interface["bin"])

tx_hash = contract.constructor().transact({"from": account, "gas": 3000000})
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

contract_addr = receipt.contractAddress
print(f"\n✓ 合约部署成功")
print(f"  合约地址: {contract_addr}")

# ============================================================
# 5. 自动上链 — 将 SHA256 哈希写入合约
# ============================================================
contract_instance = w3.eth.contract(address=contract_addr, abi=contract_interface["abi"])

tx_hash = contract_instance.functions.storeHash(sha256_hash).transact({"from": account, "gas": 300000})
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"✓ 哈希已上链")
print(f"  交易哈希: {tx_hash.hex()}")
print(f"  链上数据: {sha256_hash}")

# ============================================================
# 6. 链上验证 — 读取并比对
# ============================================================
onchain_hash = contract_instance.functions.getHash().call()

print(f"\n{'='*60}")
print(f"  链上验证结果")
print(f"{'='*60}")
print(f"  原始 CSV SHA256:  {sha256_hash}")
print(f"  链上存储的哈希:   {onchain_hash}")
print(f"  一致性验证:       {'✓ 通过' if onchain_hash == sha256_hash else '✗ 失败'}")

# ============================================================
# 7. 额外：演示篡改检测 — 修改 CSV 后哈希会变化
# ============================================================
tampered = raw_bytes + b"\n2026-05-21 11:00:00,DEV-003,999.9,999.9,999.9,999.9"
tampered_hash = hashlib.sha256(tampered).hexdigest()

print(f"\n  篡改检测演示:")
print(f"  原始哈希:   0x{sha256_hash}")
print(f"  篡改后哈希: 0x{tampered_hash}")
print(f"  哈希不同, 篡改可被检测: {'✓' if tampered_hash != sha256_hash else '✗'}")
