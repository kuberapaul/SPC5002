# Source notes

## Web orders

The web source is a storefront export owned by the ecommerce operations team.
Each row represents one web order. I parsed its day-first dates, stripped
category whitespace, converted the returned flag from `Y`/`N` to `1`/`0`, and
kept prices in pounds.

## Phone orders

The phone source is a call-centre order log owned by customer operations. Each
call contains one order. Its prices are integer pence, so I converted them to
pounds; quantities were coerced to integers, categories were stripped before
mapping to the Week 1 names, and the UTC timestamp was reduced to its date.

## CRM customers

The CRM extract is a customer master owned by the CRM team. Each row is a
customer record, although 27 customer IDs appear twice. I skipped the two
title rows, mapped 22 region spellings to the seven Week 1 region values, and
mapped `Yes`/`No` marketing opt-in values to booleans. The first row was kept
for duplicate IDs when joining.

## Marketing opt-in reconciliation

The CRM has no marketing opt-in for 23 customers who placed 46 orders. Week 1
has an opt-in on all 46 of those orders: 34 are `True` and 12 are `False`.
There is no record of who supplied these values or where they came from. I
would not fill the missing CRM values using the most common value, because
that would falsely make two systems agree and would turn unknown provenance
into asserted customer data.
