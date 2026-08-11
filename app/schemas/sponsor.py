from typing import Optional

from pydantic import BaseModel


class NiveauSponsorBase(BaseModel):
    nom: str
    ordre_affichage: int = 0
    couleur: Optional[str] = None


class NiveauSponsorCreate(NiveauSponsorBase):
    pass


class NiveauSponsor(NiveauSponsorBase):
    id: int

    class Config:
        from_attributes = True


class SponsorBase(BaseModel):
    nom: str
    logo_url: str
    lien_site: str
    niveau_id: int


class SponsorCreate(SponsorBase):
    pass


class Sponsor(SponsorBase):
    id: int
    niveau: Optional[NiveauSponsor] = None

    class Config:
        from_attributes = True