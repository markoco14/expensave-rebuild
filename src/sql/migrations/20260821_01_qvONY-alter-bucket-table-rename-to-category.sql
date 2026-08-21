-- Alter bucket table rename to category 
-- depends: 20260721_01_hzXjJ-alter-purchase-table-set-bucket-id-allow-null

ALTER TABLE bucket RENAME COLUMN bucket_id TO category_id;

ALTER TABLE bucket RENAME TO category;
