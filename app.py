from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"


@dataclass
class Tariff:
    bw_per_page: Decimal = Decimal("5.00")
    color_per_page: Decimal = Decimal("15.00")


@dataclass
class CopyJob:
    pages: int
    color: bool = False
    duplex: bool = False

    def __post_init__(self) -> None:
        if self.pages <= 0:
            raise ValueError("Количество страниц должно быть положительным")


@dataclass
class MachineState:
    paper_sheets: int = 500
    toner_bw_percent: int = 100
    toner_color_percent: int = 100
    cash_balance: Decimal = Decimal("0.00")
    print_history: list[str] = field(default_factory=list)


class CopierVendingMachine:
    """ПО для вендингового копировального аппарата «Ю.Лист»."""

    def __init__(self, name: str = "Ю.Лист", tariff: Tariff | None = None, state: MachineState | None = None) -> None:
        self.name = name
        self.tariff = tariff or Tariff()
        self.state = state or MachineState()

    def estimate_price(self, job: CopyJob) -> Decimal:
        base = self.tariff.color_per_page if job.color else self.tariff.bw_per_page
        duplex_discount = Decimal("0.90") if job.duplex else Decimal("1.00")
        amount = base * job.pages * duplex_discount
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def can_execute(self, job: CopyJob) -> tuple[bool, str]:
        if self.state.paper_sheets < job.pages:
            return False, "Недостаточно бумаги"

        required_bw = job.pages
        required_color = job.pages if job.color else 0

        if self.state.toner_bw_percent <= 0 or self.state.toner_bw_percent < required_bw // 10:
            return False, "Недостаточно черного тонера"
        if job.color and (self.state.toner_color_percent <= 0 or self.state.toner_color_percent < required_color // 10):
            return False, "Недостаточно цветного тонера"

        return True, "OK"

    def process_job(self, job: CopyJob, payment_method: PaymentMethod, payment_amount: Decimal) -> dict[str, Decimal | str | int]:
        can_run, reason = self.can_execute(job)
        if not can_run:
            raise RuntimeError(reason)

        price = self.estimate_price(job)
        if payment_amount < price:
            raise RuntimeError(f"Недостаточно средств. Стоимость: {price} ₽")

        self.state.paper_sheets -= job.pages
        self.state.toner_bw_percent = max(0, self.state.toner_bw_percent - max(1, job.pages // 10))
        if job.color:
            self.state.toner_color_percent = max(0, self.state.toner_color_percent - max(1, job.pages // 10))

        self.state.cash_balance += price
        change = (payment_amount - price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        history_row = (
            f"pages={job.pages}, color={job.color}, duplex={job.duplex}, "
            f"pay={payment_method.value}, price={price}"
        )
        self.state.print_history.append(history_row)

        return {
            "price": price,
            "change": change,
            "pages_left": self.state.paper_sheets,
            "cash_balance": self.state.cash_balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "status": "completed",
        }


if __name__ == "__main__":
    machine = CopierVendingMachine()
    demo_job = CopyJob(pages=12, color=True, duplex=True)
    result = machine.process_job(demo_job, payment_method=PaymentMethod.CARD, payment_amount=Decimal("200"))

    print(f"{machine.name}: заказ выполнен")
    print(result)
