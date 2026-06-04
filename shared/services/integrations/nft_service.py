"""
NFT 内容所有权服务
提供文章铸造 NFT、验证所有权等功能

注意：此功能需要配置 Web3 provider 和智能合约
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List


@dataclass
class NFTMetadata:
    """NFT 元数据"""
    name: str  # NFT 名称
    description: str  # 描述
    image: str = ""  # 封面图片 URL
    article_id: int = 0  # 关联的文章 ID
    author: str = ""  # 作者地址
    created_at: str = ""  # 创建时间
    attributes: List[Dict[str, Any]] = field(default_factory=list)  # 属性

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "article_id": self.article_id,
            "author": self.author,
            "created_at": self.created_at,
            "attributes": self.attributes
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def get_hash(self) -> str:
        """获取元数据的哈希值"""
        content = self.to_json()
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


@dataclass
class NFTRecord:
    """NFT 记录"""
    token_id: str  # Token ID
    contract_address: str  # 合约地址
    owner_address: str  # 所有者地址
    metadata_uri: str  # 元数据 URI
    article_id: int  # 关联文章 ID
    minted_at: str  # 铸造时间
    transaction_hash: str = ""  # 交易哈希
    network: str = "ethereum"  # 网络
    is_verified: bool = False  # 是否已验证


class NFTService:
    """
    NFT 服务
    
    功能：
    1. 生成 NFT 元数据
    2. 铸造 NFT（模拟）
    3. 验证 NFT 所有权
    4. 查询 NFT 信息
    """

    def __init__(self):
        # 模拟的 NFT 存储（实际应使用数据库）
        self.nft_records: Dict[int, NFTRecord] = {}

        # 配置（应从环境变量或配置文件读取）
        self.config = {
            "provider_url": "",  # Web3 Provider URL
            "contract_address": "",  # NFT 合约地址
            "private_key": "",  # 私钥（用于签名）
            "network": "ethereum",  # 网络：ethereum, polygon, arbitrum 等
            "ipfs_gateway": "https://ipfs.io/ipfs/"  # IPFS 网关
        }

    def generate_metadata(self, article_data: Dict[str, Any]) -> NFTMetadata:
        """
        为文章生成 NFT 元数据
        
        Args:
            article_data: 文章数据 {id, title, excerpt, cover_image, author, created_at}
            
        Returns:
            NFT 元数据对象
        """
        article_id = article_data.get("id", 0)
        title = article_data.get("title", "Untitled")
        excerpt = article_data.get("excerpt", "")
        cover_image = article_data.get("cover_image", "")
        author = article_data.get("author", "")
        created_at = article_data.get("created_at", datetime.now().isoformat())

        # 生成属性
        attributes = [
            {
                "trait_type": "Article Type",
                "value": article_data.get("type", "blog")
            },
            {
                "trait_type": "Word Count",
                "value": len(article_data.get("content", ""))
            },
            {
                "trait_type": "Created At",
                "value": created_at
            }
        ]

        # 添加标签作为属性
        tags = article_data.get("tags", [])
        if tags:
            attributes.append({
                "trait_type": "Tags",
                "value": ", ".join(tags[:5])  # 最多5个标签
            })

        metadata = NFTMetadata(
            name=f"Article #{article_id}: {title}",
            description=excerpt or f"NFT for article: {title}",
            image=cover_image,
            article_id=article_id,
            author=author,
            created_at=created_at,
            attributes=attributes
        )

        return metadata

    def mint_nft(self, article_data: Dict[str, Any], owner_address: str) -> Optional[NFTRecord]:
        """
        为文章铸造 NFT
        
        Args:
            article_data: 文章数据
            owner_address: 所有者钱包地址
            
        Returns:
            NFT 记录，失败返回 None
        """
        try:
            article_id = article_data.get("id", 0)

            # 检查是否已经铸造过
            if article_id in self.nft_records:
                print(f"⚠️ 文章 {article_id} 已经铸造过 NFT")
                return self.nft_records[article_id]

            # 生成元数据
            metadata = self.generate_metadata(article_data)

            # 在实际实现中，这里应该：
            # 1. 将元数据上传到 IPFS
            # 2. 调用智能合约铸造 NFT
            # 3. 等待交易确认

            # 模拟铸造过程
            token_id = f"{article_id}_{int(datetime.now().timestamp())}"
            metadata_uri = f"ipfs://{metadata.get_hash()}"  # 模拟 IPFS URI

            nft_record = NFTRecord(
                token_id=token_id,
                contract_address=self.config.get("contract_address", "0x0000000000000000000000000000000000000000"),
                owner_address=owner_address,
                metadata_uri=metadata_uri,
                article_id=article_id,
                minted_at=datetime.now().isoformat(),
                transaction_hash=f"0x{''.join(['0'] * 64)}",  # 模拟交易哈希
                network=self.config.get("network", "ethereum"),
                is_verified=True
            )

            # 保存记录
            self.nft_records[article_id] = nft_record

            print(f"✅ NFT 铸造成功: Token ID = {token_id}")
            print(f"   所有者: {owner_address}")
            print(f"   元数据 URI: {metadata_uri}")

            return nft_record

        except Exception as e:
            print(f"❌ NFT 铸造失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def verify_ownership(self, article_id: int, wallet_address: str) -> bool:
        """
        验证钱包地址是否拥有文章的 NFT
        
        Args:
            article_id: 文章 ID
            wallet_address: 钱包地址
            
        Returns:
            是否拥有所有权
        """
        if article_id not in self.nft_records:
            return False

        nft_record = self.nft_records[article_id]
        return nft_record.owner_address.lower() == wallet_address.lower()

    def get_nft_info(self, article_id: int) -> Optional[Dict[str, Any]]:
        """
        获取文章的 NFT 信息
        
        Args:
            article_id: 文章 ID
            
        Returns:
            NFT 信息字典，不存在返回 None
        """
        if article_id not in self.nft_records:
            return None

        record = self.nft_records[article_id]

        return {
            "token_id": record.token_id,
            "contract_address": record.contract_address,
            "owner_address": record.owner_address,
            "metadata_uri": record.metadata_uri,
            "minted_at": record.minted_at,
            "transaction_hash": record.transaction_hash,
            "network": record.network,
            "is_verified": record.is_verified,
            "opensea_url": f"https://opensea.io/assets/{record.network}/{record.contract_address}/{record.token_id}"
        }

    def get_user_nfts(self, wallet_address: str) -> List[Dict[str, Any]]:
        """
        获取用户拥有的所有 NFT
        
        Args:
            wallet_address: 钱包地址
            
        Returns:
            NFT 列表
        """
        user_nfts = []

        for article_id, record in self.nft_records.items():
            if record.owner_address.lower() == wallet_address.lower():
                user_nfts.append({
                    "article_id": article_id,
                    "token_id": record.token_id,
                    "contract_address": record.contract_address,
                    "metadata_uri": record.metadata_uri,
                    "minted_at": record.minted_at,
                    "network": record.network
                })

        return user_nfts

    def transfer_nft(self, article_id: int, new_owner_address: str) -> bool:
        """
        转移 NFT 所有权
        
        Args:
            article_id: 文章 ID
            new_owner_address: 新所有者地址
            
        Returns:
            是否转移成功
        """
        if article_id not in self.nft_records:
            print(f"❌ 文章 {article_id} 没有关联的 NFT")
            return False

        # 在实际实现中，这里应该调用智能合约的 transfer 方法

        record = self.nft_records[article_id]
        old_owner = record.owner_address
        record.owner_address = new_owner_address

        print(f"✅ NFT 所有权已转移")
        print(f"   从: {old_owner}")
        print(f"   到: {new_owner_address}")

        return True

    def upload_metadata_to_ipfs(self, metadata: NFTMetadata) -> str:
        """
        将元数据上传到 IPFS
        
        Args:
            metadata: NFT 元数据
            
        Returns:
            IPFS URI
        """
        # 在实际实现中，这里应该：
        # 1. 使用 IPFS API 上传元数据
        # 2. 获取 IPFS hash
        # 3. 返回 ipfs://{hash}

        # 模拟上传
        metadata_hash = metadata.get_hash()
        ipfs_uri = f"ipfs://{metadata_hash}"

        print(f"📤 元数据已上传到 IPFS: {ipfs_uri}")

        return ipfs_uri

    def configure(self, config: Dict[str, str]):
        """
        配置 NFT 服务
        
        Args:
            config: 配置字典
        """
        self.config.update(config)
        print("✅ NFT 服务配置已更新")


# 全局实例
nft_service = NFTService()
