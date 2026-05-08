CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE public.logs (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    user_name VARCHAR(100),
    action VARCHAR(3),
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id)
);

CREATE TABLE public.temp_hum (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    temp VARCHAR(100),
    hum VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now()
);
