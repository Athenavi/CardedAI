"""
加密货币支付服务

支持多种区块链和代币的支付处理

功能:
1. 钱包地址生成
2. 支付检测
3. 区块链确认监听
4. x402协议集成
5. NFT门票验证
6. 稳定币支付支持
"""

import hashlib
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List


class Blockchain(Enum):
    """支持的区块链网络"""
    ETHEREUM = "ethereum"
    BITCOIN = "bitcoin"
    POLYGON = "polygon"
    BINANCE_SMART_CHAIN = "bsc"
    SOLANA = "solana"


class TokenSymbol(Enum):
    """支持的代币符号"""
    ETH = "ETH"
    BTC = "BTC"
    USDT = "USDT"
    USDC = "USDC"
    MATIC = "MATIC"
    BNB = "BNB"
    SOL = "SOL"


class CryptoPaymentStatus(Enum):
    """加密货币支付状态"""
    WAITING_PAYMENT = "waiting_payment"
    DETECTING = "detecting"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class CryptoPaymentRequest:
    """加密货币支付请求"""

    def __init__(
            self,
            order_id: str,
            user_id: int,
            amount_usd: float,
            blockchain: Blockchain,
            token_symbol: TokenSymbol,
            wallet_address: str,
            exchange_rate: float,
            expires_in_minutes: int = 30
    ):
        self.order_id = order_id
        self.user_id = user_id
        self.amount_usd = amount_usd
        self.blockchain = blockchain
        self.token_symbol = token_symbol
        self.wallet_address = wallet_address
        self.exchange_rate = exchange_rate
        self.crypto_amount = amount_usd / exchange_rate if exchange_rate > 0 else 0
        self.expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
        self.status = CryptoPaymentStatus.WAITING_PAYMENT
        self.tx_hash = None
        self.confirmations = 0
        self.required_confirmations = self._get_required_confirmations(blockchain)
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

    def _get_required_confirmations(self, blockchain: Blockchain) -> int:
        """获取所需确认数"""
        confirmations_map = {
            Blockchain.BITCOIN: 6,
            Blockchain.ETHEREUM: 12,
            Blockchain.POLYGON: 128,
            Blockchain.BINANCE_SMART_CHAIN: 15,
            Blockchain.SOLANA: 32,
        }
        return confirmations_map.get(blockchain, 6)

    def is_expired(self) -> bool:
        """检查是否过期"""
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "amount_usd": self.amount_usd,
            "blockchain": self.blockchain.value,
            "token_symbol": self.token_symbol.value,
            "wallet_address": self.wallet_address,
            "exchange_rate": self.exchange_rate,
            "crypto_amount": self.crypto_amount,
            "status": self.status.value,
            "tx_hash": self.tx_hash,
            "confirmations": self.confirmations,
            "required_confirmations": self.required_confirmations,
            "expires_at": self.expires_at.isoformat(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class WalletManager:
    """
    钱包管理器

    管理加密货币钱包地址生成和验证
    """

    def __init__(self):
        self.supported_blockchains = [
            Blockchain.ETHEREUM,
            Blockchain.BITCOIN,
            Blockchain.POLYGON,
            Blockchain.BINANCE_SMART_CHAIN,
            Blockchain.SOLANA,
        ]

    def generate_deposit_address(
            self,
            user_id: int,
            blockchain: Blockchain,
            token_symbol: TokenSymbol
    ) -> str:
        """
        生成存款地址

        Args:
            user_id: 用户ID
            blockchain: 区块链网络
            token_symbol: 代币符号

        Returns:
            钱包地址
        """
        # 在实际实现中，这里应该调用相应的区块链API或钱包服务
        # 目前使用模拟地址生成
        address_seed = f"{user_id}_{blockchain.value}_{token_symbol.value}_{time.time()}"
        address_hash = hashlib.sha256(address_seed.encode()).hexdigest()

        if blockchain == Blockchain.BITCOIN:
            return f"bc1q{address_hash[:38]}"
        elif blockchain in [Blockchain.ETHEREUM, Blockchain.POLYGON, Blockchain.BINANCE_SMART_CHAIN]:
            return f"0x{address_hash[:40]}"
        elif blockchain == Blockchain.SOLANA:
            return f"Sol{address_hash[:43]}"
        else:
            return f"0x{address_hash[:40]}"

    def validate_address(self, address: str, blockchain: Blockchain) -> bool:
        """验证钱包地址格式"""
        if not address or len(address) < 10:
            return False

        if blockchain == Blockchain.BITCOIN:
            return address.startswith(("1", "3", "bc1"))
        elif blockchain in [Blockchain.ETHEREUM, Blockchain.POLYGON, Blockchain.BINANCE_SMART_CHAIN]:
            return address.startswith("0x") and len(address) == 42
        elif blockchain == Blockchain.SOLANA:
            return len(address) >= 32 and len(address) <= 44
        else:
            return False


class BlockchainExplorer:
    """
    区块链浏览器接口

    用于查询交易状态和确认数
    """

    def __init__(self, api_keys: Dict[str, str] = None):
        self.api_keys = api_keys or {}
        self.explorer_urls = {
            Blockchain.ETHEREUM: "https://api.etherscan.io/api",
            Blockchain.BITCOIN: "https://blockchain.info/rawtx",
            Blockchain.POLYGON: "https://api.polygonscan.com/api",
            Blockchain.BINANCE_SMART_CHAIN: "https://api.bscscan.com/api",
            Blockchain.SOLANA: "https://api.mainnet-beta.solana.com",
        }

    async def get_transaction_status(
            self,
            tx_hash: str,
            blockchain: Blockchain
    ) -> Dict[str, Any]:
        """
        获取交易状态

        Args:
            tx_hash: 交易哈希
            blockchain: 区块链网络

        Returns:
            交易状态信息
        """
        # 在实际实现中，这里应该调用相应的区块链浏览器API
        # 目前返回模拟数据
        return {
            "tx_hash": tx_hash,
            "blockchain": blockchain.value,
            "confirmations": 3,
            "is_confirmed": True,
            "block_number": 12345678,
            "timestamp": datetime.now().isoformat(),
            "from_address": "0x1234567890abcdef1234567890abcdef12345678",
            "to_address": "0xabcdef1234567890abcdef1234567890abcdef12",
            "value": "0.5",
            "gas_used": "21000",
        }

    async def get_confirmations(
            self,
            tx_hash: str,
            blockchain: Blockchain
    ) -> int:
        """获取交易确认数"""
        status = await self.get_transaction_status(tx_hash, blockchain)
        return status.get("confirmations", 0)

    async def listen_for_payment(
            self,
            wallet_address: str,
            expected_amount: float,
            blockchain: Blockchain,
            timeout_seconds: int = 1800
    ) -> Optional[Dict[str, Any]]:
        """
        监听支付

        Args:
            wallet_address: 钱包地址
            expected_amount: 期望金额
            blockchain: 区块链网络
            timeout_seconds: 超时时间（秒）

        Returns:
            交易信息，如果超时则返回None
        """
        # 在实际实现中，这里应该使用WebSocket或轮询来监听区块链
        # 目前返回模拟数据
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            # 模拟检测到支付
            if time.time() - start_time > 10:  # 模拟10秒后检测到支付
                return {
                    "tx_hash": f"0x{hashlib.md5(wallet_address.encode()).hexdigest()}",
                    "from_address": "0x1234567890abcdef1234567890abcdef12345678",
                    "to_address": wallet_address,
                    "amount": expected_amount,
                    "confirmations": 1,
                    "timestamp": datetime.now().isoformat(),
                }

            # 等待一段时间再检查
            await asyncio.sleep(5)

        return None


class X402ProtocolHandler:
    """
    x402协议处理器

    实现x402微支付通道协议
    """

    def __init__(self):
        self.payment_channels = {}

    async def create_payment_channel(
            self,
            sender_address: str,
            receiver_address: str,
            amount: float,
            blockchain: Blockchain
    ) -> Dict[str, Any]:
        """
        创建支付通道

        Args:
            sender_address: 发送方地址
            receiver_address: 接收方地址
            amount: 金额
            blockchain: 区块链网络

        Returns:
            支付通道信息
        """
        channel_id = f"channel_{hashlib.md5(f'{sender_address}_{receiver_address}_{time.time()}'.encode()).hexdigest()[:16]}"

        channel_info = {
            "channel_id": channel_id,
            "sender": sender_address,
            "receiver": receiver_address,
            "amount": amount,
            "blockchain": blockchain.value,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        }

        self.payment_channels[channel_id] = channel_info

        return {
            "success": True,
            "channel": channel_info,
        }

    async def process_micro_payment(
            self,
            channel_id: str,
            amount: float,
            signature: str
    ) -> Dict[str, Any]:
        """
        处理微支付

        Args:
            channel_id: 通道ID
            amount: 金额
            signature: 签名

        Returns:
            支付结果
        """
        if channel_id not in self.payment_channels:
            return {"success": False, "error": "Channel not found"}

        channel = self.payment_channels[channel_id]

        if channel["status"] != "active":
            return {"success": False, "error": "Channel is not active"}

        # 在实际实现中，这里需要验证签名
        # 目前简化处理

        return {
            "success": True,
            "payment_id": f"pay_{hashlib.md5(f'{channel_id}_{amount}_{time.time()}'.encode()).hexdigest()[:16]}",
            "amount": amount,
            "channel_id": channel_id,
            "timestamp": datetime.now().isoformat(),
        }

    async def close_channel(self, channel_id: str) -> Dict[str, Any]:
        """关闭支付通道"""
        if channel_id not in self.payment_channels:
            return {"success": False, "error": "Channel not found"}

        self.payment_channels[channel_id]["status"] = "closed"

        return {
            "success": True,
            "channel_id": channel_id,
            "closed_at": datetime.now().isoformat(),
        }


class NFTTicketVerifier:
    """
    NFT门票验证器

    验证NFT持有者身份并解锁专属内容
    """

    def __init__(self):
        self.nft_contracts = {}

    def register_nft_contract(
            self,
            contract_address: str,
            blockchain: Blockchain,
            name: str,
            required_token_ids: List[int] = None
    ):
        """
        注册NFT合约

        Args:
            contract_address: 合约地址
            blockchain: 区块链网络
            name: NFT集合名称
            required_token_ids: 必需的Token ID列表（可选）
        """
        self.nft_contracts[contract_address] = {
            "contract_address": contract_address,
            "blockchain": blockchain,
            "name": name,
            "required_token_ids": required_token_ids,
        }

    async def verify_nft_ownership(
            self,
            wallet_address: str,
            contract_address: str,
            token_id: int = None
    ) -> bool:
        """
        验证NFT所有权

        Args:
            wallet_address: 钱包地址
            contract_address: 合约地址
            token_id: Token ID（可选）

        Returns:
            是否拥有NFT
        """
        if contract_address not in self.nft_contracts:
            return False

        # 在实际实现中，这里应该调用区块链API验证NFT所有权
        # 目前返回模拟结果
        return True

    async def get_user_nfts(
            self,
            wallet_address: str,
            blockchain: Blockchain = None
    ) -> List[Dict[str, Any]]:
        """
        获取用户拥有的NFT列表

        Args:
            wallet_address: 钱包地址
            blockchain: 区块链网络（可选）

        Returns:
            NFT列表
        """
        # 在实际实现中，这里应该调用区块链API获取NFT列表
        # 目前返回模拟数据
        return [
            {
                "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
                "token_id": 1,
                "name": "FastBlog VIP Pass #1",
                "description": "Exclusive access to premium content",
                "image": "https://example.com/nft/1.png",
                "blockchain": Blockchain.ETHEREUM.value,
            }
        ]


class StablecoinPaymentProcessor:
    """
    稳定币支付处理器

    支持USDT、USDC等稳定币支付
    """

    def __init__(self):
        self.supported_stablecoins = {
            TokenSymbol.USDT: {
                "networks": [Blockchain.ETHEREUM, Blockchain.POLYGON, Blockchain.BINANCE_SMART_CHAIN],
                "decimals": 6,
            },
            TokenSymbol.USDC: {
                "networks": [Blockchain.ETHEREUM, Blockchain.POLYGON, Blockchain.SOLANA],
                "decimals": 6,
            },
        }

    async def create_payment_request(
            self,
            order_id: str,
            user_id: int,
            amount: float,
            token_symbol: TokenSymbol,
            blockchain: Blockchain
    ) -> Dict[str, Any]:
        """
        创建稳定币支付请求

        Args:
            order_id: 订单ID
            user_id: 用户ID
            amount: 金额（USD）
            token_symbol: 代币符号
            blockchain: 区块链网络

        Returns:
            支付请求信息
        """
        if token_symbol not in self.supported_stablecoins:
            return {
                "success": False,
                "error": f"Unsupported stablecoin: {token_symbol.value}"
            }

        if blockchain not in self.supported_stablecoins[token_symbol]["networks"]:
            return {
                "success": False,
                "error": f"{token_symbol.value} not supported on {blockchain.value}"
            }

        # 稳定币通常与USD 1:1挂钩
        exchange_rate = 1.0
        crypto_amount = amount / exchange_rate

        wallet_manager = WalletManager()
        deposit_address = wallet_manager.generate_deposit_address(
            user_id, blockchain, token_symbol
        )

        payment_request = CryptoPaymentRequest(
            order_id=order_id,
            user_id=user_id,
            amount_usd=amount,
            blockchain=blockchain,
            token_symbol=token_symbol,
            wallet_address=deposit_address,
            exchange_rate=exchange_rate,
        )

        return {
            "success": True,
            "payment_request": payment_request.to_dict(),
            "deposit_address": deposit_address,
            "expected_amount": crypto_amount,
            "token_symbol": token_symbol.value,
            "blockchain": blockchain.value,
        }

    async def verify_payment(
            self,
            tx_hash: str,
            blockchain: Blockchain,
            expected_amount: float,
            recipient_address: str
    ) -> Dict[str, Any]:
        """
        验证稳定币支付

        Args:
            tx_hash: 交易哈希
            blockchain: 区块链网络
            expected_amount: 期望金额
            recipient_address: 接收地址

        Returns:
            验证结果
        """
        explorer = BlockchainExplorer()
        tx_status = await explorer.get_transaction_status(tx_hash, blockchain)

        # 验证交易是否存在且已确认
        if not tx_status.get("is_confirmed"):
            return {
                "success": False,
                "error": "Transaction not confirmed",
            }

        # 验证金额和接收地址
        actual_amount = float(tx_status.get("value", 0))
        to_address = tx_status.get("to_address", "")

        if abs(actual_amount - expected_amount) > 0.01:  # 允许小额误差
            return {
                "success": False,
                "error": "Amount mismatch",
                "expected": expected_amount,
                "actual": actual_amount,
            }

        if to_address.lower() != recipient_address.lower():
            return {
                "success": False,
                "error": "Recipient address mismatch",
            }

        return {
            "success": True,
            "tx_hash": tx_hash,
            "confirmations": tx_status.get("confirmations", 0),
            "amount": actual_amount,
            "verified_at": datetime.now().isoformat(),
        }


class CryptoPaymentManager:
    """
    加密货币支付管理器

    统一管理所有加密货币支付相关功能

    架构说明：
    - 内存缓存：self.payment_requests 作为快速访问缓存
    - ORM 持久化：通过 CryptoPayment ORM 模型持久化到数据库，确保数据不丢失
    """

    def __init__(self):
        self.wallet_manager = WalletManager()
        self.blockchain_explorer = BlockchainExplorer()
        self.x402_handler = X402ProtocolHandler()
        self.nft_verifier = NFTTicketVerifier()
        self.stablecoin_processor = StablecoinPaymentProcessor()
        self.payment_requests: Dict[str, CryptoPaymentRequest] = {}

    @staticmethod
    async def _persist_to_orm(payment_request: CryptoPaymentRequest) -> bool:
        """将支付请求持久化到 ORM 模型"""
        try:
            from src.utils.database.unified_manager import db_manager
            from shared.models.crypto_payment import CryptoPayment as ORMCryptoPayment
            from sqlalchemy import select

            async with db_manager.get_async_session() as session:
                # 检查是否已存在
                existing = await session.execute(
                    select(ORMCryptoPayment).where(
                        ORMCryptoPayment.tx_hash == payment_request.order_id
                    )
                )
                if existing.scalar_one_or_none():
                    return True  # 已存在

                record = ORMCryptoPayment(
                    wallet_address=payment_request.wallet_address,
                    blockchain=payment_request.blockchain.value,
                    token_symbol=payment_request.token_symbol.value,
                    tx_hash=payment_request.order_id,  # 使用 order_id 作为唯一标识
                    confirmations=payment_request.confirmations,
                    required_confirmations=payment_request.required_confirmations,
                    exchange_rate=payment_request.exchange_rate,
                    crypto_amount=payment_request.crypto_amount,
                    status=payment_request.status.value,
                    expires_at=payment_request.expires_at,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                session.add(record)
                await session.commit()
                return True
        except Exception as e:
            from src.unified_logger import default_logger as logger
            logger.warning(f"CryptoPayment ORM 持久化失败（不影响主流程）：{e}")
            return False

    @staticmethod
    async def _update_orm_status(order_id: str, status: str, confirmations: int = 0) -> bool:
        """更新 ORM 中的支付状态"""
        try:
            from src.utils.database.unified_manager import db_manager
            from shared.models.crypto_payment import CryptoPayment as ORMCryptoPayment
            from sqlalchemy import select, update

            async with db_manager.get_async_session() as session:
                await session.execute(
                    update(ORMCryptoPayment).where(
                        ORMCryptoPayment.tx_hash == order_id
                    ).values(
                        status=status,
                        confirmations=confirmations,
                        updated_at=datetime.now()
                    )
                )
                await session.commit()
                return True
        except Exception as e:
            from src.unified_logger import default_logger as logger
            logger.warning(f"CryptoPayment ORM 状态更新失败：{e}")
            return False

    async def create_crypto_payment(
            self,
            order_id: str,
            user_id: int,
            amount_usd: float,
            blockchain: Blockchain,
            token_symbol: TokenSymbol
    ) -> Dict[str, Any]:
        """
        创建加密货币支付

        Args:
            order_id: 订单ID
            user_id: 用户ID
            amount_usd: 金额（USD）
            blockchain: 区块链网络
            token_symbol: 代币符号

        Returns:
            支付请求信息
        """
        # 获取当前汇率（在实际实现中应该从交易所API获取）
        exchange_rates = {
            TokenSymbol.ETH: 2000.0,
            TokenSymbol.BTC: 40000.0,
            TokenSymbol.USDT: 1.0,
            TokenSymbol.USDC: 1.0,
            TokenSymbol.MATIC: 0.8,
            TokenSymbol.BNB: 300.0,
            TokenSymbol.SOL: 100.0,
        }

        exchange_rate = exchange_rates.get(token_symbol, 1.0)

        # 生成存款地址
        deposit_address = self.wallet_manager.generate_deposit_address(
            user_id, blockchain, token_symbol
        )

        # 创建支付请求
        payment_request = CryptoPaymentRequest(
            order_id=order_id,
            user_id=user_id,
            amount_usd=amount_usd,
            blockchain=blockchain,
            token_symbol=token_symbol,
            wallet_address=deposit_address,
            exchange_rate=exchange_rate,
        )

        # 内存缓存
        self.payment_requests[order_id] = payment_request

        # ORM 持久化（异步，不阻塞主流程）
        await self._persist_to_orm(payment_request)

        return {
            "success": True,
            "payment_request": payment_request.to_dict(),
            "deposit_address": deposit_address,
            "qr_code_url": f"https://api.qrserver.com/v1/create-qr-code/?data={deposit_address}&size=300x300",
        }

    async def check_payment_status(self, order_id: str) -> Dict[str, Any]:
        """
        检查支付状态

        Args:
            order_id: 订单ID

        Returns:
            支付状态信息
        """
        # 优先从内存缓存获取
        payment_request = self.payment_requests.get(order_id)

        # 缓存未命中时，从 ORM 加载
        if not payment_request:
            payment_request = await self._load_from_orm(order_id)
            if payment_request:
                self.payment_requests[order_id] = payment_request

        if not payment_request:
            return {
                "success": False,
                "error": "Payment request not found",
            }

        # 检查是否过期
        if payment_request.is_expired():
            payment_request.status = CryptoPaymentStatus.EXPIRED
            await self._update_orm_status(order_id, CryptoPaymentStatus.EXPIRED.value)
            return {
                "success": True,
                "status": payment_request.to_dict(),
            }

        # 如果有交易哈希，检查确认数
        if payment_request.tx_hash:
            confirmations = await self.blockchain_explorer.get_confirmations(
                payment_request.tx_hash,
                payment_request.blockchain
            )
            payment_request.confirmations = confirmations

            if confirmations >= payment_request.required_confirmations:
                payment_request.status = CryptoPaymentStatus.COMPLETED
                await self._update_orm_status(order_id, CryptoPaymentStatus.COMPLETED.value, confirmations)

        return {
            "success": True,
            "status": payment_request.to_dict(),
        }

    @staticmethod
    async def _load_from_orm(order_id: str) -> Optional[CryptoPaymentRequest]:
        """从 ORM 加载支付请求"""
        try:
            from src.utils.database.unified_manager import db_manager
            from shared.models.crypto_payment import CryptoPayment as ORMCryptoPayment
            from sqlalchemy import select

            async with db_manager.get_async_session() as session:
                result = await session.execute(
                    select(ORMCryptoPayment).where(ORMCryptoPayment.tx_hash == order_id)
                )
                record = result.scalar_one_or_none()

                if not record:
                    return None

                # 将 ORM 记录转换为 CryptoPaymentRequest
                blockchain = Blockchain(record.blockchain) if record.blockchain else Blockchain.ETHEREUM
                token_symbol = TokenSymbol(record.token_symbol) if record.token_symbol else TokenSymbol.USDT

                req = CryptoPaymentRequest(
                    order_id=order_id,
                    user_id=0,  # ORM 中没有 user_id，使用默认值
                    amount_usd=float(record.crypto_amount or 0) * float(record.exchange_rate or 1),
                    blockchain=blockchain,
                    token_symbol=token_symbol,
                    wallet_address=record.wallet_address or "",
                    exchange_rate=float(record.exchange_rate or 1),
                )
                req.status = CryptoPaymentStatus(
                    record.status) if record.status else CryptoPaymentStatus.WAITING_PAYMENT
                req.confirmations = record.confirmations or 0
                req.tx_hash = record.tx_hash if record.tx_hash != order_id else None
                return req
        except Exception as e:
            from src.unified_logger import default_logger as logger
            logger.warning(f"从 ORM 加载 CryptoPayment 失败：{e}")
            return None

    async def process_webhook(
            self,
            blockchain: Blockchain,
            payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理区块链webhook

        Args:
            blockchain: 区块链网络
            payload: webhook数据

        Returns:
            处理结果
        """
        # 在实际实现中，这里需要验证webhook签名并处理事件
        event_type = payload.get("event")

        if event_type == "transaction_confirmed":
            tx_hash = payload.get("tx_hash")
            confirmations = payload.get("confirmations", 0)
            # 查找相关的支付请求并更新状态
            for order_id, payment_request in self.payment_requests.items():
                if payment_request.tx_hash == tx_hash:
                    payment_request.status = CryptoPaymentStatus.COMPLETED
                    payment_request.confirmations = confirmations
                    # 同步更新 ORM
                    await self._update_orm_status(order_id, CryptoPaymentStatus.COMPLETED.value, confirmations)
                    return {"success": True, "order_id": order_id}

        return {"success": False, "error": "Event not processed"}


# 全局实例
crypto_payment_manager = CryptoPaymentManager()
