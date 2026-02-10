from decimal import Decimal

from app import CopierVendingMachine, CopyJob, PaymentMethod


def test_estimate_price_bw():
    machine = CopierVendingMachine()
    price = machine.estimate_price(CopyJob(pages=10, color=False, duplex=False))
    assert price == Decimal("50.00")


def test_estimate_price_color_duplex_discount():
    machine = CopierVendingMachine()
    price = machine.estimate_price(CopyJob(pages=10, color=True, duplex=True))
    assert price == Decimal("135.00")


def test_process_job_with_change():
    machine = CopierVendingMachine()
    result = machine.process_job(
        CopyJob(pages=5, color=False), payment_method=PaymentMethod.CASH, payment_amount=Decimal("30")
    )
    assert result["price"] == Decimal("25.00")
    assert result["change"] == Decimal("5.00")
    assert result["status"] == "completed"


def test_process_job_insufficient_funds_raises():
    machine = CopierVendingMachine()
    try:
        machine.process_job(
            CopyJob(pages=20, color=True), payment_method=PaymentMethod.CARD, payment_amount=Decimal("10")
        )
        assert False, "Expected RuntimeError"
    except RuntimeError as err:
        assert "Недостаточно средств" in str(err)
