"""
Wallet Model for MongoDB
Collection: wallets
"""
from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime


class WalletModel(Document):
    """User wallet for fund management stored in MongoDB"""
    
    # User reference
    user_id: str = Field(..., description="Reference to the user")
    
    # Balance
    balance: float = Field(default=0.0, ge=0, description="Current wallet balance")
    currency: str = Field(default="USD", description="Currency code")
    
    # Transaction history tracking
    total_added: float = Field(default=0.0, ge=0, description="Total funds ever added")
    total_spent: float = Field(default=0.0, ge=0, description="Total funds ever spent")
    transaction_count: int = Field(default=0, ge=0, description="Total number of transactions")
    
    # Last transaction info
    last_transaction_id: Optional[str] = Field(None, description="Last transaction ID")
    last_transaction_at: Optional[datetime] = Field(None, description="Timestamp of last transaction")
    last_transaction_type: Optional[str] = Field(None, description="Type of last transaction (add/spend)")
    last_transaction_amount: Optional[float] = Field(None, description="Amount of last transaction")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "wallets"
        indexes = [
            "user_id",
        ]
