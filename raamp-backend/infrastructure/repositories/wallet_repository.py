"""
Wallet Repository
Handles CRUD operations for wallets collection
"""
from typing import Optional
from datetime import datetime
from infrastructure.database.models.wallet_model import WalletModel


class WalletRepository:
    """Repository for wallet operations"""
    
    async def get_by_user_id(self, user_id: str) -> Optional[WalletModel]:
        """Get wallet for a user"""
        return await WalletModel.find_one(
            WalletModel.user_id == user_id
        )
    
    async def get_or_create(self, user_id: str) -> WalletModel:
        """Get existing wallet or create a new one with zero balance"""
        existing = await self.get_by_user_id(user_id)
        
        if existing:
            return existing
        
        # Create new wallet with zero balance
        wallet = WalletModel(
            user_id=user_id,
            balance=0.0,
            currency="USD",
            total_added=0.0,
            total_spent=0.0,
            transaction_count=0
        )
        await wallet.insert()
        return wallet
    
    async def add_funds(
        self,
        user_id: str,
        amount: float,
        transaction_id: str
    ) -> WalletModel:
        """Add funds to user's wallet"""
        wallet = await self.get_or_create(user_id)
        
        # Update wallet
        wallet.balance += amount
        wallet.total_added += amount
        wallet.transaction_count += 1
        wallet.last_transaction_id = transaction_id
        wallet.last_transaction_at = datetime.utcnow()
        wallet.last_transaction_type = "add"
        wallet.last_transaction_amount = amount
        wallet.updated_at = datetime.utcnow()
        
        await wallet.save()
        return wallet
    
    async def spend_funds(
        self,
        user_id: str,
        amount: float,
        transaction_id: str
    ) -> Optional[WalletModel]:
        """Spend funds from user's wallet (returns None if insufficient balance)"""
        wallet = await self.get_or_create(user_id)
        
        # Check sufficient balance
        if wallet.balance < amount:
            return None
        
        # Update wallet
        wallet.balance -= amount
        wallet.total_spent += amount
        wallet.transaction_count += 1
        wallet.last_transaction_id = transaction_id
        wallet.last_transaction_at = datetime.utcnow()
        wallet.last_transaction_type = "spend"
        wallet.last_transaction_amount = amount
        wallet.updated_at = datetime.utcnow()
        
        await wallet.save()
        return wallet
    
    async def get_balance(self, user_id: str) -> float:
        """Get current balance for a user"""
        wallet = await self.get_by_user_id(user_id)
        return wallet.balance if wallet else 0.0
