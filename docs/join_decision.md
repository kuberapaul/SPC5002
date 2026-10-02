# Join decision

The storefront and phone readers produce 1,900 and 96 orders respectively.
After concatenation there are 1,996 orders. The CRM extract contains 1,088
rows for 1,061 distinct customers. Twenty-seven customer IDs occur more than
once. Those customers account for 34 orders, so joining the raw CRM would
duplicate those orders and violate the intended many-to-one relationship.

I first attempted the join with `validate="many_to_one"` so that pandas would
prove the CRM key was not unique. It raised a merge error as expected. I chose
to keep the first CRM row for each duplicated customer ID, then performed the
validated left join using the resulting 1,061-row customer table. This keeps
all 1,996 orders and produces one joined row per order.

Keeping the first row is a reproducible choice, but it is not proof that the
first record is the correct one. If I could ask the CRM owner, I would ask why
these customer IDs have multiple records, which record is current, and whether
the conflicting region, tenure, or marketing opt-in values should be merged or
corrected at source. A future extract should provide a stable customer key and
an explicit current-record indicator.
