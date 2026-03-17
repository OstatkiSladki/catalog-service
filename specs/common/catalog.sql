-- CATALOG SERVICE - db_catalog
-- Таблицы: categories, products, product_categories, offers, offer_items, reviews

CREATE SCHEMA IF NOT EXISTS "catalog";

CREATE TYPE "catalog"."offer_status" AS ENUM ('active', 'sold_out', 'expired', 'cancelled');


CREATE TABLE "catalog"."categories" (
    "id" BIGSERIAL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "slug" VARCHAR(100) NOT NULL UNIQUE,
    "parent_id" BIGINT,
    "is_active" BOOLEAN DEFAULT TRUE,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "deleted_at" TIMESTAMP WITH TIME ZONE,
    CONSTRAINT "fk_categories_parent" FOREIGN KEY ("parent_id") REFERENCES "catalog"."categories"("id") ON DELETE SET NULL
);
CREATE INDEX "categories_idx_parent" ON "catalog"."categories" ("parent_id");


CREATE TABLE "catalog"."products" (
    "id" BIGSERIAL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "image_urls" JSONB DEFAULT '[]',
    "characteristics_json" JSONB DEFAULT '{}',
    "is_active" BOOLEAN DEFAULT TRUE,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "deleted_at" TIMESTAMP WITH TIME ZONE
);
CREATE INDEX "products_idx_active" ON "catalog"."products" ("is_active", "deleted_at");


CREATE TABLE "catalog"."product_categories" (
    "id" BIGSERIAL PRIMARY KEY,
    "product_id" BIGINT NOT NULL,
    "category_id" BIGINT NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("product_id", "category_id"),
    CONSTRAINT "fk_pc_product" FOREIGN KEY ("product_id") REFERENCES "catalog"."products"("id") ON DELETE CASCADE,
    CONSTRAINT "fk_pc_category" FOREIGN KEY ("category_id") REFERENCES "catalog"."categories"("id") ON DELETE CASCADE
);
CREATE INDEX "product_categories_idx_product" ON "catalog"."product_categories" ("product_id");
CREATE INDEX "product_categories_idx_category" ON "catalog"."product_categories" ("category_id");


CREATE TABLE "catalog"."offers" (
    "id" BIGSERIAL PRIMARY KEY,
    "venue_id" BIGINT NOT NULL, 
    "current_price" DECIMAL(10, 2) NOT NULL,
    "original_price" DECIMAL(10, 2) NOT NULL,
    "quantity_available" INTEGER NOT NULL DEFAULT 1,
    "expires_at" TIMESTAMP WITH TIME ZONE NOT NULL,
    "status" offer_status DEFAULT 'active',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX "offers_idx_venue" ON "catalog"."offers" ("venue_id", "status");
CREATE INDEX "offers_idx_expires" ON "catalog"."offers" ("expires_at");
CREATE INDEX "offers_idx_status" ON "catalog"."offers" ("status");


CREATE TABLE "catalog"."offer_items" (
    "id" BIGSERIAL PRIMARY KEY,
    "offer_id" BIGINT NOT NULL,
    "product_id" BIGINT NOT NULL,
    "quantity" INTEGER NOT NULL DEFAULT 1,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("offer_id", "product_id"),
    CONSTRAINT "fk_oi_offer" FOREIGN KEY ("offer_id") REFERENCES "catalog"."offers"("id") ON DELETE CASCADE,
    CONSTRAINT "fk_oi_product" FOREIGN KEY ("product_id") REFERENCES "catalog"."products"("id") ON DELETE CASCADE
);
CREATE INDEX "offer_items_idx_offer" ON "catalog"."offer_items" ("offer_id");
CREATE INDEX "offer_items_idx_product" ON "catalog"."offer_items" ("product_id");


CREATE TABLE "catalog"."reviews" (
    "id" BIGSERIAL PRIMARY KEY,
    "user_id" BIGINT NOT NULL, 
    "venue_id" BIGINT NOT NULL,
    "order_id" BIGINT NOT NULL UNIQUE, 
    "rating" INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    "comment" TEXT,
    "images_json" JSONB DEFAULT '[]',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "deleted_at" TIMESTAMP WITH TIME ZONE
);
CREATE INDEX "reviews_idx_venue" ON "catalog"."reviews" ("venue_id", "rating");
CREATE INDEX "reviews_idx_user" ON "catalog"."reviews" ("user_id");
CREATE INDEX "reviews_idx_order" ON "catalog"."reviews" ("order_id");


CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON "catalog"."products" FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_offers_updated_at BEFORE UPDATE ON "catalog"."offers" FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
