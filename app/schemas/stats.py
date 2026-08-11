from pydantic import BaseModel


class CategoryStat(BaseModel):
    category_id: int
    name: str
    quota: int
    sold: int
    fill_rate: float  # pourcentage, ex: 42.5


class DashboardStats(BaseModel):
    total_users: int
    total_tickets_valid: int
    total_tickets_cancelled: int
    total_rooms_capacity: int
    categories: list[CategoryStat]