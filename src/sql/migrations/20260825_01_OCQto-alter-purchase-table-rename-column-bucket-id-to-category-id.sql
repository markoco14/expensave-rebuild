-- Alter purchase table rename column bucket id to category id 
-- depends: 20260821_01_qvONY-alter-bucket-table-rename-to-category

ALTER TABLE purchase RENAME COLUMN bucket_id TO category_id;