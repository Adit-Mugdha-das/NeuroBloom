from sqlmodel import SQLModel

from app.core.config import engine
from app.models.risk_alert import RiskAlert


def main():
	SQLModel.metadata.create_all(engine, tables=[RiskAlert.__table__], checkfirst=True)
	print("risk_alerts table verified")


if __name__ == "__main__":
	main()