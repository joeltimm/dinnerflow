--
-- PostgreSQL database dump
--

\restrict HKLhj2WAmpfTplKtjlzHxdZyrF8HmEnEg5BJv6AbXBuc9IlDAsVqvGGVDF1LNei

-- Dumped from database version 15.15 (Debian 15.15-1.pgdg12+1)
-- Dumped by pg_dump version 15.15 (Debian 15.15-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: cooking_log; Type: TABLE; Schema: public; Owner: dinneruser
--

CREATE TABLE public.cooking_log (
    id integer NOT NULL,
    recipe_id integer,
    date_cooked date DEFAULT CURRENT_DATE,
    rating integer,
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT cooking_log_rating_check CHECK (((rating >= 1) AND (rating <= 5)))
);


ALTER TABLE public.cooking_log OWNER TO dinneruser;

--
-- Name: cooking_log_id_seq; Type: SEQUENCE; Schema: public; Owner: dinneruser
--

CREATE SEQUENCE public.cooking_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cooking_log_id_seq OWNER TO dinneruser;

--
-- Name: cooking_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dinneruser
--

ALTER SEQUENCE public.cooking_log_id_seq OWNED BY public.cooking_log.id;


--
-- Name: recipes; Type: TABLE; Schema: public; Owner: dinneruser
--

CREATE TABLE public.recipes (
    id integer NOT NULL,
    title text NOT NULL,
    source_url text,
    entry_method text DEFAULT 'scraped'::text,
    ingredients jsonb,
    instructions jsonb,
    full_text_content text,
    local_image_path text,
    embedding public.vector(1536),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    rating integer,
    last_cooked timestamp without time zone,
    times_cooked integer DEFAULT 0,
    is_favorite boolean DEFAULT false,
    user_id integer
);


ALTER TABLE public.recipes OWNER TO dinneruser;

--
-- Name: recipes_id_seq; Type: SEQUENCE; Schema: public; Owner: dinneruser
--

CREATE SEQUENCE public.recipes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.recipes_id_seq OWNER TO dinneruser;

--
-- Name: recipes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dinneruser
--

ALTER SEQUENCE public.recipes_id_seq OWNED BY public.recipes.id;


--
-- Name: search_terms; Type: TABLE; Schema: public; Owner: dinneruser
--

CREATE TABLE public.search_terms (
    id integer NOT NULL,
    term text NOT NULL,
    category text,
    last_used_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    user_id integer
);


ALTER TABLE public.search_terms OWNER TO dinneruser;

--
-- Name: search_terms_id_seq; Type: SEQUENCE; Schema: public; Owner: dinneruser
--

CREATE SEQUENCE public.search_terms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.search_terms_id_seq OWNER TO dinneruser;

--
-- Name: search_terms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dinneruser
--

ALTER SEQUENCE public.search_terms_id_seq OWNED BY public.search_terms.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: dinneruser
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email text NOT NULL,
    password_hash text NOT NULL,
    full_name text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.users OWNER TO dinneruser;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: dinneruser
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO dinneruser;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dinneruser
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: cooking_log id; Type: DEFAULT; Schema: public; Owner: dinneruser
--

ALTER TABLE ONLY public.cooking_log ALTER COLUMN id SET DEFAULT nextval('public.cooking_log_id_seq'::regclass);


--
-- Name: recipes id; Type: DEFAULT; Schema: public; Owner: dinneruser
--

ALTER TABLE ONLY public.recipes ALTER COLUMN id SET DEFAULT nextval('public.recipes_id_seq'::regclass);


--
-- Name: search_terms id; Type: DEFAULT; Schema: public; Owner: dinneruser
--

ALTER TABLE ONLY public.search_terms ALTER COLUMN id SET DEFAULT nextval('public.search_terms_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: dinneruser
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: cooking_log; Type: TABLE DATA; Schema: public; Owner: dinneruser
--

COPY public.cooking_log (id, recipe_id, date_cooked, rating, notes, created_at) FROM stdin;
\.


--
-- Data for Name: recipes; Type: TABLE DATA; Schema: public; Owner: dinneruser
--

COPY public.recipes (id, title, source_url, entry_method, ingredients, instructions, full_text_content, local_image_path, embedding, created_at, rating, last_cooked, times_cooked, is_favorite, user_id) FROM stdin;
1	test		manual	\N	\N	test		\N	2025-12-07 20:07:32.045371	1	\N	0	f	1
\.


--
-- Data for Name: search_terms; Type: TABLE DATA; Schema: public; Owner: dinneruser
--

COPY public.search_terms (id, term, category, last_used_at, created_at, user_id) FROM stdin;
6	Margherita Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
7	Spaghetti Carbonara (Traditional or Chicken/Turkey Bacon)	Italian	\N	2025-12-07 20:53:14.566347	1
8	Bean Enchiladas	Mexican	\N	2025-12-07 20:53:14.566347	1
10	Beef Stroganoff	Comfort Food	\N	2025-12-07 20:53:14.566347	1
100	Tebasaki (Japanese Chicken Wings, Main Portion)	Asian	\N	2025-12-07 20:53:14.566347	1
106	Korean-Style Pork Meatballs	Asian	\N	2025-12-07 20:53:14.566347	1
295	Chicken and Zucchini Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
391	Chicken and Bacon Carbonara	Italian	\N	2025-12-07 20:53:14.566347	1
392	Spicy Ground Pork Tacos	Mexican	\N	2025-12-07 20:53:14.566347	1
573	Pork and Cabbage Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
9	Chicken Souvlaki Plate	Mediterranean	\N	2025-12-07 20:53:14.566347	1
11	Crispy Tofu Bowl with Peanut Sauce	Asian	\N	2025-12-07 20:53:14.566347	1
12	Eggplant Parmesan	Italian	\N	2025-12-07 20:53:14.566347	1
13	Thai Green Curry (Chicken/Tofu/Vegetable)	Asian	\N	2025-12-07 20:53:14.566347	1
14	Sheet Pan Fajitas (Chicken/Steak/Veg)	Mexican	\N	2025-12-07 20:53:14.566347	1
15	Turkey Chili	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
16	Baked Ziti	Italian	\N	2025-12-07 20:53:14.566347	1
17	Pork Chops (Seared or Baked)	Pork	\N	2025-12-07 20:53:14.566347	1
18	Hearty Quinoa Salad (Main Dish Size)	Salad	\N	2025-12-07 20:53:14.566347	1
19	Butter Chicken	Indian	\N	2025-12-07 20:53:14.566347	1
20	Vegetable Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
21	Beef Bulgogi Bowl	Asian	\N	2025-12-07 20:53:14.566347	1
22	Chicken Marsala	Italian	\N	2025-12-07 20:53:14.566347	1
23	Lentil Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
24	Stuffed Bell Peppers (Beef/Rice/Veg)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
25	Chicken Piccata	Italian	\N	2025-12-07 20:53:14.566347	1
26	Beef Tacos	Mexican	\N	2025-12-07 20:53:14.566347	1
27	Buttermilk Fried Chicken with Honey Glaze	Comfort Food	\N	2025-12-07 20:53:14.566347	1
28	Gourmet Meatloaf with Balsamic Ketchup	Comfort Food	\N	2025-12-07 20:53:14.566347	1
29	Smoked Pulled Pork with Apple Cider Slaw	Pork	\N	2025-12-07 20:53:14.566347	1
30	Pan-Seared Duck Breast with Cherry Reduction	Poultry	\N	2025-12-07 20:53:14.566347	1
31	Braised Short Ribs with Creamy Polenta	Meat	\N	2025-12-07 20:53:14.566347	1
32	Pork Belly Tacos with Pineapple Salsa	Mexican	\N	2025-12-07 20:53:14.566347	1
33	Spicy Chorizo Mac and Cheese	Comfort Food	\N	2025-12-07 20:53:14.566347	1
34	Truffle Mushroom Pizza with Arugula	Italian	\N	2025-12-07 20:53:14.566347	1
35	Nashville Hot Chicken Sandwich Plate	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
36	Lamb Shank with Root Vegetable Purée	Meat	\N	2025-12-07 20:53:14.566347	1
37	Deconstructed Chicken Pot Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
38	Bone-in Pork Chops with Bourbon Sauce	Pork	\N	2025-12-07 20:53:14.566347	1
39	Turkey Meatballs with Pesto Cream Sauce	Italian	\N	2025-12-07 20:53:14.566347	1
40	Sweet Tea-Brined Chicken	Poultry	\N	2025-12-07 20:53:14.566347	1
41	Cajun Chicken Pasta (Creamy or Spicy)	Italian	\N	2025-12-07 20:53:14.566347	1
42	Sauerbraten (German Pot Roast)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
43	Chicken and Waffles with Maple Syrup Gravy	Comfort Food	\N	2025-12-07 20:53:14.566347	1
44	Hanger Steak with Chimichurri and Fingerlings	Meat	\N	2025-12-07 20:53:14.566347	1
45	Black Bean Burger on Pretzel Bun	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
46	Adobo-Rubbed Pork Shoulder	Pork	\N	2025-12-07 20:53:14.566347	1
47	Gnocchi with Brown Butter Sage Sauce	Italian	\N	2025-12-07 20:53:14.566347	1
48	Vegetarian Poutine (Main Dish Portion)	Vegetarian	\N	2025-12-07 20:53:14.566347	1
49	Muffuletta Sandwich (Main Dish Size)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
50	Smoked Turkey Legs with Collard Greens	Poultry	\N	2025-12-07 20:53:14.566347	1
51	Chicken and Dumplings	Comfort Food	\N	2025-12-07 20:53:14.566347	1
52	Mapo Tofu (Pork/Veg)	Asian	\N	2025-12-07 20:53:14.566347	1
53	Pork Vindaloo	Indian	\N	2025-12-07 20:53:14.566347	1
54	Pork Schnitzel with Lemon	Pork	\N	2025-12-07 20:53:14.566347	1
55	Chicken Fried Steak with Cream Gravy	Meat	\N	2025-12-07 20:53:14.566347	1
56	Pork Tenderloin with Mustard Glaze	Pork	\N	2025-12-07 20:53:14.566347	1
57	Bison Burger with Smoked Gouda	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
58	Kielbasa and Cabbage	Comfort Food	\N	2025-12-07 20:53:14.566347	1
59	Lamb Korma	Indian	\N	2025-12-07 20:53:14.566347	1
60	Vegetable Biryani	Indian	\N	2025-12-07 20:53:14.566347	1
61	Chiles en Nogada (Meat or Veg)	Mexican	\N	2025-12-07 20:53:14.566347	1
62	Cuban Sandwich (Pressed, large size)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
63	Chicken Shawarma Plate	Mediterranean	\N	2025-12-07 20:53:14.566347	1
64	Mushroom Wellington	Vegetarian	\N	2025-12-07 20:53:14.566347	1
65	Classic Pot Roast with Carrots and Potatoes	Comfort Food	\N	2025-12-07 20:53:14.566347	1
66	Philly Cheesesteak (Authentic Roll)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
67	Brunswick Stew (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
68	Jagerschnitzel with Mushroom Gravy	Pork	\N	2025-12-07 20:53:14.566347	1
69	Perogies with Caramelized Onions and Sour Cream	Comfort Food	\N	2025-12-07 20:53:14.566347	1
70	Massaman Curry (Beef or Chicken)	Asian	\N	2025-12-07 20:53:14.566347	1
71	Albondigas Soup (Main Dish Size)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
72	Chicken Cacciatore	Italian	\N	2025-12-07 20:53:14.566347	1
73	Blackened Chicken with Dirty Rice	Poultry	\N	2025-12-07 20:53:14.566347	1
74	Chicken Katsu	Asian	\N	2025-12-07 20:53:14.566347	1
75	Beef Bourguignon	French	\N	2025-12-07 20:53:14.566347	1
76	Pork Ragu over Pappardelle	Italian	\N	2025-12-07 20:53:14.566347	1
77	Stuffed Cabbage Rolls	Comfort Food	\N	2025-12-07 20:53:14.566347	1
78	Hot Brown Sandwich (Louisville Specialty)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
79	Taco Salad (Beef/Chicken/Bean, Main Size)	Mexican	\N	2025-12-07 20:53:14.566347	1
80	Moussaka (Beef/Lamb)	Mediterranean	\N	2025-12-07 20:53:14.566347	1
81	Fasolia (Greek White Bean Stew)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
82	Spicy Dan Dan Noodles (Pork/Veg)	Asian	\N	2025-12-07 20:53:14.566347	1
83	Chicken Paprikash	Comfort Food	\N	2025-12-07 20:53:14.566347	1
84	Arroz con Pollo	Mexican	\N	2025-12-07 20:53:14.566347	1
85	Torta Ahogada (Pork)	Mexican	\N	2025-12-07 20:53:14.566347	1
86	Tamales (Pork/Chicken/Cheese)	Mexican	\N	2025-12-07 20:53:14.566347	1
87	Calzone (Meat/Veg)	Italian	\N	2025-12-07 20:53:14.566347	1
88	Khachapuri (Georgian Cheese Bread, Main Size)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
89	Cottage Pie (Beef Mince)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
90	Pastitsio (Greek Baked Pasta)	Italian	\N	2025-12-07 20:53:14.566347	1
91	Jambalaya (Chicken/Sausage)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
92	Okonomiyaki (Japanese Savory Pancake)	Asian	\N	2025-12-07 20:53:14.566347	1
93	Pad See Ew (Beef/Chicken)	Asian	\N	2025-12-07 20:53:14.566347	1
94	Galbi Jjim (Korean Braised Short Ribs)	Asian	\N	2025-12-07 20:53:14.566347	1
95	Frikadeller (Danish Meatballs)	Meat	\N	2025-12-07 20:53:14.566347	1
96	Mole Poblano (Chicken/Turkey)	Mexican	\N	2025-12-07 20:53:14.566347	1
97	Cassoulet (Pork/Duck/Beans)	French	\N	2025-12-07 20:53:14.566347	1
98	Confit de Canard (Duck Confit)	French	\N	2025-12-07 20:53:14.566347	1
99	Coq au Vin	French	\N	2025-12-07 20:53:14.566347	1
2	Creamy Mushroom Risotto	Italian	2025-12-07 20:55:37.828567	2025-12-07 20:53:14.566347	1
101	New American Hotdish (Tater Tot Casserole)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
102	Gourmet Sloppy Joes with Brioche Buns	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
103	Bacon-Wrapped Meatloaf with Sweet Glaze	Comfort Food	\N	2025-12-07 20:53:14.566347	1
104	Short Rib Grilled Cheese on Sourdough	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
105	Chicken Spiedini with Lemon-Garlic Sauce	Italian	\N	2025-12-07 20:53:14.566347	1
107	Buffalo Chicken Mac and Cheese	Comfort Food	\N	2025-12-07 20:53:14.566347	1
108	Green Chile Chicken Enchiladas	Mexican	\N	2025-12-07 20:53:14.566347	1
109	Homestyle Chicken and Biscuits	Comfort Food	\N	2025-12-07 20:53:14.566347	1
110	Pork Osso Buco over Saffron Risotto	Italian	\N	2025-12-07 20:53:14.566347	1
111	Smoked Brisket Plate with BBQ Beans	Meat	\N	2025-12-07 20:53:14.566347	1
113	Pan-Seared Halloumi with Roasted Vegetables	Vegetarian	\N	2025-12-07 20:53:14.566347	1
114	Chicken Tinga Tostadas	Mexican	\N	2025-12-07 20:53:14.566347	1
115	Pork Milanese with Arugula Salad	Italian	\N	2025-12-07 20:53:14.566347	1
116	Sweet Potato and Black Bean Burritos	Mexican	\N	2025-12-07 20:53:14.566347	1
117	Spicy Sausage and Kale Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
118	Chicken Tortilla Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
119	Lamb Kofta with Tzatziki and Pita	Mediterranean	\N	2025-12-07 20:53:14.566347	1
120	Chicken Picadillo	Mexican	\N	2025-12-07 20:53:14.566347	1
121	Butternut Squash and Sage Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
122	Spicy Gochujang Tofu with Kimchi Fried Rice	Asian	\N	2025-12-07 20:53:14.566347	1
123	Italian Wedding Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
124	French Onion Pot Roast	Comfort Food	\N	2025-12-07 20:53:14.566347	1
125	Cuban Mojo Pork	Pork	\N	2025-12-07 20:53:14.566347	1
126	Vegetarian Bolognese with Zucchini Noodles	Italian	\N	2025-12-07 20:53:14.566347	1
127	Pork and Hominy Posole	Mexican	\N	2025-12-07 20:53:14.566347	1
128	Chicken Scampi (Garlic Butter Sauce, No Seafood)	Italian	\N	2025-12-07 20:53:14.566347	1
129	Creamy Turkey and Wild Rice Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
130	Crockpot Mississippi Pot Roast	Comfort Food	\N	2025-12-07 20:53:14.566347	1
131	Chicken Kiev	Comfort Food	\N	2025-12-07 20:53:14.566347	1
132	Vegan Shepherd's Pie (Lentil Base)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
133	Stuffed Poblano Peppers (Cheese/Chicken/Beef)	Mexican	\N	2025-12-07 20:53:14.566347	1
134	Honey Garlic Glazed Pork Ribs	Pork	\N	2025-12-07 20:53:14.566347	1
135	Chicken Curry with Roti	Indian	\N	2025-12-07 20:53:14.566347	1
136	Spicy Italian Sausage and Peppers	Italian	\N	2025-12-07 20:53:14.566347	1
137	Peruvian Aji de Gallina (Chicken)	South American	\N	2025-12-07 20:53:14.566347	1
138	Spicy Black Bean Soup with Avocado	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
139	Chicken Saltimbocca	Italian	\N	2025-12-07 20:53:14.566347	1
140	Beef and Guinness Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
141	Tuscan Butter Chicken	Italian	\N	2025-12-07 20:53:14.566347	1
142	Chicken and Chorizo Paella (No Seafood)	Spanish	\N	2025-12-07 20:53:14.566347	1
143	Khinkali (Georgian Meat Dumplings)	Asian	\N	2025-12-07 20:53:14.566347	1
144	Mushroom Stroganoff (Vegetarian)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
145	Chicken Tagine with Couscous	African	\N	2025-12-07 20:53:14.566347	1
146	Vietnamese Caramelized Pork and Eggs	Asian	\N	2025-12-07 20:53:14.566347	1
147	Chicken Teriyaki Bowl with Rice	Asian	\N	2025-12-07 20:53:14.566347	1
148	Spicy Peanut Noodles (Chicken/Tofu)	Asian	\N	2025-12-07 20:53:14.566347	1
149	Korean Pork Bossam	Asian	\N	2025-12-07 20:53:14.566347	1
150	Zesty Lemon Herb Chicken	Poultry	\N	2025-12-07 20:53:14.566347	1
151	Turkey Pot Pie with Puff Pastry	Comfort Food	\N	2025-12-07 20:53:14.566347	1
152	Grilled Chicken with Pomegranate Molasses	Poultry	\N	2025-12-07 20:53:14.566347	1
153	Butternut Squash and Ricotta Cannelloni	Italian	\N	2025-12-07 20:53:14.566347	1
154	Spicy Chicken Stir-fry with Cashews	Asian	\N	2025-12-07 20:53:14.566347	1
155	Chicken Tikka Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
156	Classic Beef Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
157	Chicken Fajita Casserole	Mexican	\N	2025-12-07 20:53:14.566347	1
158	Spicy Szechuan Noodles with Ground Pork	Asian	\N	2025-12-07 20:53:14.566347	1
159	Cuban Picadillo (Beef)	South American	\N	2025-12-07 20:53:14.566347	1
160	Vegetable Korma	Indian	\N	2025-12-07 20:53:14.566347	1
161	Chicken Gordon Bleu	Comfort Food	\N	2025-12-07 20:53:14.566347	1
162	New England Style Boiled Dinner (Corned Beef)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
163	Turkey Club Wrap (Main Size)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
164	BBQ Chicken Pizza (New American Style)	Italian	\N	2025-12-07 20:53:14.566347	1
165	Pork Chop Casserole with Potatoes	Comfort Food	\N	2025-12-07 20:53:14.566347	1
167	Chicken Parmigiana Sandwich (Main Dish Size)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
168	Mexican Street Corn Chicken Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
169	Slow Cooker Chicken Adobo	Asian	\N	2025-12-07 20:53:14.566347	1
170	Pork Souvlaki with Lemon Potatoes	Mediterranean	\N	2025-12-07 20:53:14.566347	1
171	Vegetable Pot Stickers (Main Portion)	Asian	\N	2025-12-07 20:53:14.566347	1
172	Chicken Jalfrezi	Indian	\N	2025-12-07 20:53:14.566347	1
173	Cajun Gumbo (Chicken/Andouille Sausage - No Seafood)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
174	Goulash (Hungarian Style, Beef)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
175	French Lentil and Sausage Stew	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
176	Sweet and Sour Pork	Asian	\N	2025-12-07 20:53:14.566347	1
177	Spicy Chicken Lo Mein	Asian	\N	2025-12-07 20:53:14.566347	1
178	Greek Lemon Chicken and Orzo	Mediterranean	\N	2025-12-07 20:53:14.566347	1
179	Mushroom and Swiss Burger (Gourmet)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
180	Chicken Milanese with Tomato Salad	Italian	\N	2025-12-07 20:53:14.566347	1
181	Ramen with Pork Belly and Soft-Boiled Egg	Asian	\N	2025-12-07 20:53:14.566347	1
182	Chilaquiles (Breakfast-for-Dinner)	Mexican	\N	2025-12-07 20:53:14.566347	1
183	Vegan Meatball Sub Sandwich	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
184	Chicken Pot Pie Soup with Biscuits	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
185	Blackened Tofu with Mango Salsa	Vegetarian	\N	2025-12-07 20:53:14.566347	1
186	Pork Gyoza (Main Portion)	Asian	\N	2025-12-07 20:53:14.566347	1
187	Chicken and Black Bean Skillet	Mexican	\N	2025-12-07 20:53:14.566347	1
188	Spicy Peanut Chicken Skewers	Asian	\N	2025-12-07 20:53:14.566347	1
189	Beef Rendang	Asian	\N	2025-12-07 20:53:14.566347	1
190	Chicken Shawarma Wrap (Main Size)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
191	Mushroom Risotto with Truffle Oil	Italian	\N	2025-12-07 20:53:14.566347	1
192	Lamb Curry	Indian	\N	2025-12-07 20:53:14.566347	1
193	Chicken Chimichangas	Mexican	\N	2025-12-07 20:53:14.566347	1
194	Hearty Split Pea Soup with Ham (Main Dish)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
195	Chicken A La King	Comfort Food	\N	2025-12-07 20:53:14.566347	1
196	Cheesy Ham and Potato Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
197	Spicy Vegetable Curry	Indian	\N	2025-12-07 20:53:14.566347	1
198	Chicken Banh Mi Sandwich	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
199	Pork Lo Mein	Asian	\N	2025-12-07 20:53:14.566347	1
200	Chicken Alfredo Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
201	Meatball Stuffed Shells	Italian	\N	2025-12-07 20:53:14.566347	1
202	Grilled Steak with Compound Butter	Meat	\N	2025-12-07 20:53:14.566347	1
203	Vegetarian Thai Basil Stir-Fry	Asian	\N	2025-12-07 20:53:14.566347	1
204	Spicy Chicken Fried Rice	Asian	\N	2025-12-07 20:53:14.566347	1
205	Pork Cordon Bleu	Comfort Food	\N	2025-12-07 20:53:14.566347	1
206	Chicken Enchiladas with White Sauce	Mexican	\N	2025-12-07 20:53:14.566347	1
207	Spicy Chicken Noodle Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
208	Beef Quesadillas	Mexican	\N	2025-12-07 20:53:14.566347	1
209	Spinach and Feta Stuffed Chicken Breast	Poultry	\N	2025-12-07 20:53:14.566347	1
210	Homestyle Chicken Noodle Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
211	Spicy Ground Beef and Potato Skillet	Comfort Food	\N	2025-12-07 20:53:14.566347	1
212	Chicken and Sausage Jambalaya	Comfort Food	\N	2025-12-07 20:53:14.566347	1
213	Portobello Mushroom Steak	Vegetarian	\N	2025-12-07 20:53:14.566347	1
214	Spicy Korean Fried Chicken	Asian	\N	2025-12-07 20:53:14.566347	1
215	Chicken Tikka Skewers	Indian	\N	2025-12-07 20:53:14.566347	1
216	Beef and Bean Burritos	Mexican	\N	2025-12-07 20:53:14.566347	1
217	Spicy Peanut Tofu Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
218	Chicken and Broccoli Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
219	Mushroom Bourguignon	French	\N	2025-12-07 20:53:14.566347	1
220	Creamy Tomato Pasta with Grilled Chicken	Italian	\N	2025-12-07 20:53:14.566347	1
221	Pork Tenderloin with Apple Chutney	Pork	\N	2025-12-07 20:53:14.566347	1
222	Spicy Chicken and Rice Bowl	Comfort Food	\N	2025-12-07 20:53:14.566347	1
223	Beef Chimichanga	Mexican	\N	2025-12-07 20:53:14.566347	1
224	Chicken and Black Bean Chili	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
225	Sweet Potato and Kale Gratin (Hearty Veg)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
226	Spicy Chicken and Veggie Skewers	Poultry	\N	2025-12-07 20:53:14.566347	1
227	Pork Katsu Curry	Asian	\N	2025-12-07 20:53:14.566347	1
228	Chicken and Mushroom Pot Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
229	Beef Rouladen	German	\N	2025-12-07 20:53:14.566347	1
230	Tofu Curry with Basmati Rice	Indian	\N	2025-12-07 20:53:14.566347	1
231	Spicy Black Bean Burgers	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
232	Chicken Pesto Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
233	Pork Stir Fry with Snow Peas	Asian	\N	2025-12-07 20:53:14.566347	1
234	Beef and Vegetable Stew	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
235	Chicken and Wild Rice Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
236	Spicy Chipotle Chicken Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
237	Chicken and Asparagus Crepes (Savory Main)	French	\N	2025-12-07 20:53:14.566347	1
238	Spicy Garlic Noodles with Chicken	Asian	\N	2025-12-07 20:53:14.566347	1
239	Pork Adobo	Asian	\N	2025-12-07 20:53:14.566347	1
240	Beef and Broccoli Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
241	Chicken and Vegetable Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
242	Spicy Korean Pork Bulgogi	Asian	\N	2025-12-07 20:53:14.566347	1
243	Chicken and White Bean Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
244	Spicy Kung Pao Tofu	Asian	\N	2025-12-07 20:53:14.566347	1
245	Pork and Bean Chili	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
246	Beef Kofta Curry	Indian	\N	2025-12-07 20:53:14.566347	1
247	Chicken and Artichoke Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
248	Spicy Indian Dal (Lentil Curry)	Indian	\N	2025-12-07 20:53:14.566347	1
249	Chicken and Sausage Gumbo (No Seafood)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
250	Pork and Sauerkraut	German	\N	2025-12-07 20:53:14.566347	1
251	Beef and Mushroom Gravy over Mashed Potatoes	Comfort Food	\N	2025-12-07 20:53:14.566347	1
252	Chicken and Sun-Dried Tomato Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
253	Spicy Chicken and Black Bean Tostadas	Mexican	\N	2025-12-07 20:53:14.566347	1
254	Chicken and Gnocchi Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
255	Spicy Sriracha Chicken Wings (Main Portion)	Poultry	\N	2025-12-07 20:53:14.566347	1
256	Pork and Sweet Potato Hash (Dinner Hash)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
257	Beef and Cheese Manicotti	Italian	\N	2025-12-07 20:53:14.566347	1
258	Chicken and Broccoli Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
259	Spicy Tofu Tacos	Mexican	\N	2025-12-07 20:53:14.566347	1
260	Chicken and Rice Pilaf (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
261	Spicy Blackened Pork Chops	Pork	\N	2025-12-07 20:53:14.566347	1
262	Pork and Spinach Stuffed Shells	Italian	\N	2025-12-07 20:53:14.566347	1
263	Beef and Cheddar Sliders (Main Portion)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
264	Chicken and Feta Stuffed Pitas	Mediterranean	\N	2025-12-07 20:53:14.566347	1
265	Spicy Cajun Sausage and Rice	Comfort Food	\N	2025-12-07 20:53:14.566347	1
266	Chicken and Quinoa Bowl with Tahini Dressing	Salad	\N	2025-12-07 20:53:14.566347	1
267	Spicy Korean Beef and Tofu Soup	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
268	Pork and Zucchini Skewers	Pork	\N	2025-12-07 20:53:14.566347	1
269	Beef and Barley Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
270	Chicken and Pesto Flatbread	Italian	\N	2025-12-07 20:53:14.566347	1
271	Spicy Chipotle Black Bean Soup	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
272	Chicken and Roasted Vegetable Medley (Main)	Poultry	\N	2025-12-07 20:53:14.566347	1
273	Spicy Pork Belly Rice Bowl	Asian	\N	2025-12-07 20:53:14.566347	1
274	Beef and Potato Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
275	Chicken and Dumpling Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
276	Spicy Tofu Katsu	Asian	\N	2025-12-07 20:53:14.566347	1
277	Chicken and Bacon Ranch Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
278	Spicy Beef Nachos (Main Dish)	Mexican	\N	2025-12-07 20:53:14.566347	1
279	Pork and Apple Meatloaf	Comfort Food	\N	2025-12-07 20:53:14.566347	1
280	Beef and Bean Chili Mac	Comfort Food	\N	2025-12-07 20:53:14.566347	1
281	Chicken and Tomato Bruschetta Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
282	Spicy Chickpea and Vegetable Tagine	African	\N	2025-12-07 20:53:14.566347	1
283	Chicken and Chorizo Risotto (No Seafood)	Italian	\N	2025-12-07 20:53:14.566347	1
284	Spicy Glazed Tofu Skewers	Vegetarian	\N	2025-12-07 20:53:14.566347	1
285	Pork and Pepper Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
286	Beef and Green Bean Casserole (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
287	Chicken and Wild Mushroom Ragout	Comfort Food	\N	2025-12-07 20:53:14.566347	1
288	Spicy Peanut Chicken Curry	Indian	\N	2025-12-07 20:53:14.566347	1
289	Chicken and Waffle Sliders (Main Portion)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
290	Spicy Black Bean and Corn Salsa Bowl (Veg)	Mexican	\N	2025-12-07 20:53:14.566347	1
291	Pork and Chorizo Meatballs	Italian	\N	2025-12-07 20:53:14.566347	1
292	Beef and Broccoli Lo Mein	Asian	\N	2025-12-07 20:53:14.566347	1
293	Chicken and Swiss Cheese Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
294	Spicy Indian Curry with Vegetables	Indian	\N	2025-12-07 20:53:14.566347	1
296	Spicy Tofu Scramble with Tortillas (Dinner)	Mexican	\N	2025-12-07 20:53:14.566347	1
297	Pork and Cabbage Rolls	Comfort Food	\N	2025-12-07 20:53:14.566347	1
298	Beef and Eggplant Curry	Indian	\N	2025-12-07 20:53:14.566347	1
299	Chicken and Red Pepper Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
300	Spicy Blackened Chicken Caesar Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
301	Chicken and Mushroom Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
302	Spicy Pork Chili	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
303	Beef and Potato Hash (Dinner)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
304	Chicken and Spinach Stuffed Shells	Italian	\N	2025-12-07 20:53:14.566347	1
305	Spicy Chickpea and Spinach Curry	Indian	\N	2025-12-07 20:53:14.566347	1
306	Chicken and White Wine Sauce Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
307	Spicy Ground Turkey Skillet	Comfort Food	\N	2025-12-07 20:53:14.566347	1
308	Pork and Black Bean Burrito Bowl	Mexican	\N	2025-12-07 20:53:14.566347	1
309	Beef and Cheese Enchiladas	Mexican	\N	2025-12-07 20:53:14.566347	1
310	Chicken and Cauliflower Curry	Indian	\N	2025-12-07 20:53:14.566347	1
311	Spicy Tofu and Vegetable Skewers	Vegetarian	\N	2025-12-07 20:53:14.566347	1
312	Chicken and Butternut Squash Risotto	Italian	\N	2025-12-07 20:53:14.566347	1
313	Spicy Beef and Broccoli Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
314	Pork and Leek Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
315	Beef and Kidney Bean Chili	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
316	Chicken and Sweet Potato Curry	Indian	\N	2025-12-07 20:53:14.566347	1
317	Spicy Peanut Tofu Noodles	Asian	\N	2025-12-07 20:53:14.566347	1
318	Chicken and Roasted Red Pepper Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
319	Spicy Pork Tostadas	Mexican	\N	2025-12-07 20:53:14.566347	1
320	Beef and Mushroom Stew	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
321	Chicken and Pesto Stromboli	Italian	\N	2025-12-07 20:53:14.566347	1
322	Spicy Chickpea and Tomato Stew	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
323	Chicken and Black Olive Tapenade Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
324	Spicy Ground Chicken Tacos	Mexican	\N	2025-12-07 20:53:14.566347	1
325	Pork and Pineapple Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
326	Beef and Cabbage Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
327	Chicken and Asparagus Risotto	Italian	\N	2025-12-07 20:53:14.566347	1
328	Spicy Vegetarian Chili	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
329	Chicken and Roasted Root Vegetables (Main)	Poultry	\N	2025-12-07 20:53:14.566347	1
330	Spicy Korean Beef Bowl	Asian	\N	2025-12-07 20:53:14.566347	1
331	Pork and Mushroom Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
332	Beef and Vegetable Pot Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
333	Chicken and Spinach Fettuccine Alfredo	Italian	\N	2025-12-07 20:53:14.566347	1
334	Spicy Tofu Fajitas	Mexican	\N	2025-12-07 20:53:14.566347	1
335	Chicken and Bell Pepper Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
336	Spicy Ground Beef Shepherd's Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
337	Pork and Black Bean Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
338	Beef and Onion Focaccia Sandwich (Main)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
339	Chicken and Roasted Garlic Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
340	Spicy Chickpea Burgers	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
341	Chicken and Artichoke Heart Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
342	Spicy Pork and Bean Burritos	Mexican	\N	2025-12-07 20:53:14.566347	1
344	Chicken and Sun-Dried Tomato Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
345	Spicy Tofu and Noodle Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
346	Pork and Leek Gratin (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
347	Beef and Tomato Ragu with Polenta	Italian	\N	2025-12-07 20:53:14.566347	1
348	Chicken and Mushroom Crepes (Savory Main)	French	\N	2025-12-07 20:53:14.566347	1
349	Spicy Black Bean and Vegetable Enchiladas	Mexican	\N	2025-12-07 20:53:14.566347	1
350	Chicken and Broccoli Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
351	Spicy Beef Stir Fry with Peanut Sauce	Asian	\N	2025-12-07 20:53:14.566347	1
352	Pork and Apple Sausage Rolls (Main Portion)	Pork	\N	2025-12-07 20:53:14.566347	1
353	Beef and Potato Gratin (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
354	Chicken and Roasted Pepper Sandwich (Main)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
355	Spicy Chickpea Masala	Indian	\N	2025-12-07 20:53:14.566347	1
356	Chicken and Spinach Ravioli with Cream Sauce	Italian	\N	2025-12-07 20:53:14.566347	1
357	Spicy Ground Pork Lo Mein	Asian	\N	2025-12-07 20:53:14.566347	1
358	Pork and Fennel Sausage Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
359	Beef and Beer Stew	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
360	Chicken and Wild Mushroom Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
361	Spicy Tofu and Veggie Curry	Indian	\N	2025-12-07 20:53:14.566347	1
362	Chicken and White Wine Mushroom Sauce (Main)	Poultry	\N	2025-12-07 20:53:14.566347	1
363	Spicy Chicken and Corn Chowder (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
364	Pork and Black Pudding (Dinner)	Pork	\N	2025-12-07 20:53:14.566347	1
365	Beef and Blue Cheese Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
366	Chicken and Roasted Vegetable Skewers	Poultry	\N	2025-12-07 20:53:14.566347	1
367	Spicy Indian Aloo Gobi (Cauliflower & Potato)	Indian	\N	2025-12-07 20:53:14.566347	1
368	Chicken and Black Bean Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
369	Spicy Ground Turkey Chili	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
370	Pork and Pepper Calzone	Italian	\N	2025-12-07 20:53:14.566347	1
371	Beef and Stout Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
372	Chicken and Lemon Herb Potatoes (Main)	Poultry	\N	2025-12-07 20:53:14.566347	1
373	Spicy Tofu and Broccoli Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
374	Chicken and Artichoke Pasta Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
375	Spicy Pork and Potato Stew	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
376	Beef and Mushroom Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
377	Chicken and Zucchini Boat (Stuffed)	Poultry	\N	2025-12-07 20:53:14.566347	1
378	Spicy Chickpea and Kale Curry	Indian	\N	2025-12-07 20:53:14.566347	1
379	Chicken and Sweet Corn Fritters (Main Dish)	Poultry	\N	2025-12-07 20:53:14.566347	1
380	Spicy Ground Beef Tostadas	Mexican	\N	2025-12-07 20:53:14.566347	1
381	Pork and Sage Meatballs	Italian	\N	2025-12-07 20:53:14.566347	1
382	Beef and Tomato Braise	Meat	\N	2025-12-07 20:53:14.566347	1
383	Chicken and Pesto Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
384	Spicy Tofu and Peanut Satay Skewers	Asian	\N	2025-12-07 20:53:14.566347	1
385	Chicken and Green Bean Casserole (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
386	Spicy Chicken and Rice Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
387	Pork and Apple Cider Glaze (Main)	Pork	\N	2025-12-07 20:53:14.566347	1
388	Beef and Bean Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
389	Chicken and Roasted Tomato Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
390	Spicy Chickpea and Lentil Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
393	Pork and Vegetable Skillet	Pork	\N	2025-12-07 20:53:14.566347	1
394	Beef and Caramelized Onion Tart (Main Dish)	Meat	\N	2025-12-07 20:53:14.566347	1
395	Chicken and Wild Rice Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
396	Spicy Tofu and Coconut Curry	Indian	\N	2025-12-07 20:53:14.566347	1
397	Chicken and Broccoli Alfredo Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
398	Spicy Beef and Bean Burrito Bowl	Mexican	\N	2025-12-07 20:53:14.566347	1
399	Pork and Mushroom Ragout	Comfort Food	\N	2025-12-07 20:53:14.566347	1
400	Beef and Mushroom Risotto	Italian	\N	2025-12-07 20:53:14.566347	1
401	Chicken and Spinach Quiche (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
402	Spicy Chickpea and Sweet Potato Stew	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
404	Spicy Ground Turkey Meatloaf	Comfort Food	\N	2025-12-07 20:53:14.566347	1
405	Pork and Green Bean Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
406	Beef and Potato Fritters (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
407	Chicken and Black Bean Burgers	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
408	Spicy Tofu and Pepper Skewers	Vegetarian	\N	2025-12-07 20:53:14.566347	1
409	Chicken and Cheese Stuffed Mushrooms (Main)	Poultry	\N	2025-12-07 20:53:14.566347	1
410	Spicy Chicken and Vegetable Curry	Indian	\N	2025-12-07 20:53:14.566347	1
411	Pork and Onion Gravy with Mash	Comfort Food	\N	2025-12-07 20:53:14.566347	1
412	Beef and Tomato Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
413	Chicken and Sun-Dried Tomato Risotto	Italian	\N	2025-12-07 20:53:14.566347	1
414	Spicy Chickpea and Cauliflower Bake	Vegetarian	\N	2025-12-07 20:53:14.566347	1
415	Chicken and Basil Pesto Sandwich (Main)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
416	Spicy Ground Beef Empanadas (Main Portion)	Mexican	\N	2025-12-07 20:53:14.566347	1
417	Pork and Mushroom Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
418	Beef and Potato Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
419	Chicken and Leek Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
420	Spicy Tofu and Quinoa Bowl	Asian	\N	2025-12-07 20:53:14.566347	1
421	Chicken and Pesto Stuffed Peppers	Italian	\N	2025-12-07 20:53:14.566347	1
422	Spicy Chicken and Black Bean Burrito	Mexican	\N	2025-12-07 20:53:14.566347	1
423	Pork and Apple Sausage Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
424	Beef and Vegetable Lo Mein	Asian	\N	2025-12-07 20:53:14.566347	1
425	Chicken and Roasted Vegetable Tart (Main)	Poultry	\N	2025-12-07 20:53:14.566347	1
426	Spicy Chickpea and Corn Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
427	Chicken and Mushroom Pot Roast	Comfort Food	\N	2025-12-07 20:53:14.566347	1
428	Spicy Ground Turkey Meatballs	Italian	\N	2025-12-07 20:53:14.566347	1
429	Pork and Cheese Quesadillas	Mexican	\N	2025-12-07 20:53:14.566347	1
431	Chicken and Wild Rice Bake	Comfort Food	\N	2025-12-07 20:53:14.566347	1
432	Spicy Tofu and Broccoli Bake	Vegetarian	\N	2025-12-07 20:53:14.566347	1
433	Chicken and Artichoke Heart Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
434	Spicy Chicken and Rice Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
435	Pork and Apple Calzone	Italian	\N	2025-12-07 20:53:14.566347	1
436	Beef and Potato Latkes (Dinner)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
437	Chicken and Bacon Melt Sandwich (Main)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
438	Spicy Chickpea and Spinach Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
439	Chicken and Sun-Dried Tomato Pesto Sandwich (Main)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
440	Spicy Ground Beef Chili Cheese Fries (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
441	Pork and Pineapple Tacos	Mexican	\N	2025-12-07 20:53:14.566347	1
442	Beef and Beer Cheese Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
443	Chicken and Roasted Bell Pepper Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
444	Spicy Tofu and Peanut Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
445	Chicken and Mushroom Alfredo	Italian	\N	2025-12-07 20:53:14.566347	1
446	Spicy Chicken and Vegetable Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
447	Pork and Sweet Potato Curry	Indian	\N	2025-12-07 20:53:14.566347	1
448	Beef and Potato Pancakes (Dinner)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
449	Chicken and Spinach Stuffed Chicken Breast	Poultry	\N	2025-12-07 20:53:14.566347	1
450	Spicy Chickpea and Tomato Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
451	Chicken and Wild Mushroom Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
452	Spicy Ground Turkey Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
453	Pork and Black Eyed Peas (Dinner)	Pork	\N	2025-12-07 20:53:14.566347	1
454	Beef and Bacon Burger (Gourmet)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
455	Chicken and Roasted Pepper Dip (Main with Bread)	Poultry	\N	2025-12-07 20:53:14.566347	1
456	Spicy Tofu and Black Bean Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
457	Chicken and Cheese Calzone	Italian	\N	2025-12-07 20:53:14.566347	1
458	Spicy Chicken and Vegetable Skillet	Poultry	\N	2025-12-07 20:53:14.566347	1
459	Pork and Mushroom Stuffed Pork Tenderloin	Pork	\N	2025-12-07 20:53:14.566347	1
460	Beef and Potato Stew (Hearty)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
461	Chicken and Roasted Garlic Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
462	Spicy Chickpea and Red Pepper Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
463	Chicken and Bacon Pasta Bake	Italian	\N	2025-12-07 20:53:14.566347	1
464	Spicy Ground Beef and Rice Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
465	Pork and Apple Stuffed Peppers	Pork	\N	2025-12-07 20:53:14.566347	1
466	Beef and Cheese Stuffed Peppers	Comfort Food	\N	2025-12-07 20:53:14.566347	1
467	Chicken and Spinach and Feta Tart (Main Dish)	Poultry	\N	2025-12-07 20:53:14.566347	1
468	Spicy Tofu and Noodle Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
469	Chicken and Mushroom Quiche (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
470	Spicy Chicken and Sweet Potato Hash (Dinner Hash)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
471	Pork and Zucchini Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
472	Beef and Mushroom Wellington	Meat	\N	2025-12-07 20:53:14.566347	1
473	Chicken and Wild Rice Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
474	Spicy Chickpea and Coconut Rice	Indian	\N	2025-12-07 20:53:14.566347	1
475	Chicken and Artichoke Heart Dip (Main with Bread)	Poultry	\N	2025-12-07 20:53:14.566347	1
476	Spicy Ground Turkey Stuffed Peppers	Comfort Food	\N	2025-12-07 20:53:14.566347	1
477	Pork and Black Bean Chili	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
478	Beef and Cheese Quesadillas	Mexican	\N	2025-12-07 20:53:14.566347	1
479	Chicken and Broccoli Quiche (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
480	Spicy Tofu and Vegetable Rice Bowl	Asian	\N	2025-12-07 20:53:14.566347	1
481	Chicken and Asparagus Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
482	Spicy Chicken and Mushroom Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
483	Pork and Apple Pie (Savory Main)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
484	Beef and Potato Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
485	Chicken and Sun-Dried Tomato Flatbread	Italian	\N	2025-12-07 20:53:14.566347	1
486	Spicy Chickpea and Kale Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
487	Chicken and Wild Mushroom Quiche (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
488	Spicy Ground Beef and Black Bean Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
489	Pork and Fennel Sausage Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
490	Beef and Vegetable Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
491	Chicken and Roasted Corn Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
492	Spicy Tofu and Peanut Sauce Pasta	Asian	\N	2025-12-07 20:53:14.566347	1
493	Chicken and Pesto Chicken Breast (Stuffed)	Italian	\N	2025-12-07 20:53:14.566347	1
494	Spicy Chicken and Zucchini Noodles	Italian	\N	2025-12-07 20:53:14.566347	1
495	Pork and Black Bean Tostadas	Mexican	\N	2025-12-07 20:53:14.566347	1
496	Beef and Onion Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
497	Chicken and Artichoke Dip Pasta (Main)	Italian	\N	2025-12-07 20:53:14.566347	1
498	Spicy Chickpea and Sweet Potato Curry	Indian	\N	2025-12-07 20:53:14.566347	1
499	Chicken and Bacon Potato Bake (Main)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
500	Spicy Ground Turkey and Rice Skillet	Comfort Food	\N	2025-12-07 20:53:14.566347	1
501	Pork and Mushroom Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
502	Beef and Roasted Beet Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
503	Chicken and Spinach and Ricotta Cannelloni	Italian	\N	2025-12-07 20:53:14.566347	1
504	Spicy Tofu and Vegetable Wraps	Vegetarian	\N	2025-12-07 20:53:14.566347	1
505	Chicken and Tomato and Basil Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
506	Spicy Chicken and Black Bean Chili Mac	Comfort Food	\N	2025-12-07 20:53:14.566347	1
507	Pork and Apple Stuffed Pork Chops	Pork	\N	2025-12-07 20:53:14.566347	1
508	Beef and Cheese Tart (Main Dish)	Meat	\N	2025-12-07 20:53:14.566347	1
509	Chicken and Wild Rice Stuffed Peppers	Comfort Food	\N	2025-12-07 20:53:14.566347	1
510	Spicy Chickpea and Quinoa Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
511	Chicken and Roasted Red Pepper Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
512	Spicy Ground Beef and Tomato Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
513	Pork and Cabbage Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
514	Beef and Bean and Corn Skillet	Mexican	\N	2025-12-07 20:53:14.566347	1
515	Chicken and Zucchini Frittata (Main Dish)	Poultry	\N	2025-12-07 20:53:14.566347	1
516	Spicy Tofu and Ginger Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
517	Chicken and Mushroom and Spinach Quiche (Main)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
518	Spicy Chicken and Roasted Vegetables	Poultry	\N	2025-12-07 20:53:14.566347	1
519	Pork and Green Chili Stew	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
520	Beef and Broccoli and Rice Bowl	Asian	\N	2025-12-07 20:53:14.566347	1
521	Chicken and Sun-Dried Tomato Pesto Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
522	Spicy Chickpea and Lentil Patties (Main Dish)	Vegetarian	\N	2025-12-07 20:53:14.566347	1
523	Chicken and Bacon and Tomato Sandwich (Main)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
524	Spicy Ground Turkey and Sweet Potato Skillet	Comfort Food	\N	2025-12-07 20:53:14.566347	1
525	Pork and Apple Burger (Gourmet)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
526	Beef and Mushroom Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
527	Chicken and Roasted Garlic and Herb Chicken Breast	Poultry	\N	2025-12-07 20:53:14.566347	1
528	Spicy Tofu and Mushroom Skewers	Vegetarian	\N	2025-12-07 20:53:14.566347	1
529	Chicken and Cheese and Broccoli Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
530	Spicy Chicken and Broccoli Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
531	Pork and Pineapple Fried Rice	Asian	\N	2025-12-07 20:53:14.566347	1
532	Beef and Potato Pancakes with Sour Cream (Dinner)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
533	Chicken and Spinach and Artichoke Dip Pasta (Main)	Italian	\N	2025-12-07 20:53:14.566347	1
534	Spicy Chickpea and Vegetable Medley	Vegetarian	\N	2025-12-07 20:53:14.566347	1
535	Chicken and Wild Rice and Mushroom Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
536	Spicy Ground Beef and Bean Burrito	Mexican	\N	2025-12-07 20:53:14.566347	1
537	Pork and Apple Stuffed Acorn Squash	Pork	\N	2025-12-07 20:53:14.566347	1
538	Beef and Cheese Stuffed Shells	Italian	\N	2025-12-07 20:53:14.566347	1
539	Chicken and Roasted Root Vegetable Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
540	Spicy Tofu and Black Bean Chili	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
541	Chicken and Pesto and Mozzarella Panini (Main)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
542	Spicy Chicken and Kale Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
543	Pork and Mushroom and Leek Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
544	Beef and Onion Rings Burger (Gourmet)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
545	Chicken and Sun-Dried Tomato and Feta Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
546	Spicy Chickpea and Spinach Dip (Main with Bread)	Vegetarian	\N	2025-12-07 20:53:14.566347	1
547	Chicken and Bacon and Cheese Quiche (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
548	Spicy Ground Turkey Meatball Sub (Main Dish)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
549	Pork and Vegetable Curry	Indian	\N	2025-12-07 20:53:14.566347	1
550	Beef and Potato Curry	Indian	\N	2025-12-07 20:53:14.566347	1
551	Chicken and Roasted Butternut Squash Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
552	Spicy Tofu and Black Eyed Peas (Dinner)	Vegetarian	\N	2025-12-07 20:53:14.566347	1
553	Chicken and Mushroom and Cheese Omelet (Dinner)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
554	Spicy Chicken and Artichoke Dip Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
555	Pork and Apple and Sage Meatloaf	Comfort Food	\N	2025-12-07 20:53:14.566347	1
556	Beef and Bean Enchiladas	Mexican	\N	2025-12-07 20:53:14.566347	1
557	Chicken and Wild Rice and Broccoli Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
558	Spicy Chickpea and Roasted Vegetable Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
559	Chicken and Pesto and Tomato Flatbread	Italian	\N	2025-12-07 20:53:14.566347	1
560	Spicy Ground Beef and Cheese Stuffed Shells	Italian	\N	2025-12-07 20:53:14.566347	1
561	Pork and Pineapple Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
562	Beef and Potato Casserole with Cheese	Comfort Food	\N	2025-12-07 20:53:14.566347	1
563	Chicken and Spinach and Mushroom Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
564	Spicy Tofu and Broccoli Casserole	Vegetarian	\N	2025-12-07 20:53:14.566347	1
565	Chicken and Roasted Pepper and Onion Skewers	Poultry	\N	2025-12-07 20:53:14.566347	1
566	Spicy Chicken and Sun-Dried Tomato Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
567	Pork and Mushroom and Spinach Stuffed Pork Tenderloin	Pork	\N	2025-12-07 20:53:14.566347	1
568	Beef and Cheese Stuffed Manicotti	Italian	\N	2025-12-07 20:53:14.566347	1
569	Chicken and Wild Rice and Carrot Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
570	Spicy Chickpea and Tomato Sauce with Polenta	Italian	\N	2025-12-07 20:53:14.566347	1
571	Chicken and Bacon and Leek Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
572	Spicy Ground Turkey and Vegetable Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
574	Beef and Tomato and Mushroom Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
575	Chicken and Sun-Dried Tomato and Spinach Quiche (Main)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
576	Spicy Tofu and Artichoke Heart Dip (Main with Bread)	Vegetarian	\N	2025-12-07 20:53:14.566347	1
577	Chicken and Pesto and Roasted Red Pepper Sandwich (Main)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
578	Spicy Chicken and Feta Stuffed Pitas	Mediterranean	\N	2025-12-07 20:53:14.566347	1
579	Pork and Apple and Cheddar Calzone	Italian	\N	2025-12-07 20:53:14.566347	1
580	Beef and Potato and Carrot Stew	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
581	Chicken and Wild Rice and Celery Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
582	Spicy Chickpea and Lentil Stew	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
583	Chicken and Bacon and Avocado Sandwich (Main)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
584	Spicy Ground Beef and Onion Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
585	Pork and Pineapple and Pepper Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
586	Beef and Cheese and Potato Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
587	Chicken and Spinach and Mushroom Alfredo	Italian	\N	2025-12-07 20:53:14.566347	1
588	Spicy Tofu and Zucchini Noodles	Italian	\N	2025-12-07 20:53:14.566347	1
589	Chicken and Roasted Asparagus Risotto	Italian	\N	2025-12-07 20:53:14.566347	1
590	Spicy Chicken and Black Olive Tapenade Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
591	Pork and Apple and Onion Meatloaf	Comfort Food	\N	2025-12-07 20:53:14.566347	1
592	Beef and Bean and Tomato Chili	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
593	Chicken and Wild Rice and Leek Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
594	Spicy Chickpea and Roasted Red Pepper Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
595	Chicken and Bacon and Tomato Quiche (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
596	Spicy Ground Turkey and Spinach Stuffed Shells	Italian	\N	2025-12-07 20:53:14.566347	1
597	Pork and Mushroom and Onion Gravy with Mash	Comfort Food	\N	2025-12-07 20:53:14.566347	1
598	Beef and Cheese and Onion Tart (Main Dish)	Meat	\N	2025-12-07 20:53:14.566347	1
599	Chicken and Sun-Dried Tomato and Artichoke Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
600	Spicy Tofu and Mushroom Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
601	Chicken and Pesto and Broccoli Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
602	Spicy Chicken and Chorizo Risotto (No Seafood)	Italian	\N	2025-12-07 20:53:14.566347	1
603	Pork and Apple and Cranberry Stuffed Pork Chops	Pork	\N	2025-12-07 20:53:14.566347	1
604	Beef and Potato and Mushroom Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
605	Chicken and Wild Rice and Corn Chowder (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
606	Spicy Chickpea and Vegetable Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
607	Chicken and Bacon and Mushroom Alfredo	Italian	\N	2025-12-07 20:53:14.566347	1
608	Spicy Ground Beef and Potato Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
609	Pork and Pineapple and Ham Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
610	Beef and Cheese and Vegetable Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
611	Chicken and Spinach and Feta Stuffed Chicken Breast	Poultry	\N	2025-12-07 20:53:14.566347	1
612	Spicy Tofu and Black Bean Burgers	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
614	Spicy Chicken and Apple Cider Glaze (Main)	Poultry	\N	2025-12-07 20:53:14.566347	1
615	Pork and Mushroom and Swiss Burger (Gourmet)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
616	Beef and Onion and Cheese Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
617	Chicken and Sun-Dried Tomato and Spinach Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
618	Spicy Chickpea and Quinoa Bowl	Salad	\N	2025-12-07 20:53:14.566347	1
619	Chicken and Pesto and Zucchini Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
620	Spicy Ground Turkey and Black Bean Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
621	Pork and Apple and Sage Stuffed Acorn Squash	Pork	\N	2025-12-07 20:53:14.566347	1
622	Beef and Cheese and Broccoli Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
623	Chicken and Wild Rice and Butternut Squash Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
624	Spicy Tofu and Roasted Root Vegetables (Main)	Vegetarian	\N	2025-12-07 20:53:14.566347	1
625	Chicken and Bacon and Onion Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
626	Spicy Chicken and Black Bean Burrito Bowl	Mexican	\N	2025-12-07 20:53:14.566347	1
627	Pork and Mushroom and Potato Gratin (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
628	Beef and Cheese and Potato Fritters (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
629	Chicken and Sun-Dried Tomato and Artichoke Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
630	Spicy Chickpea and Tomato and Spinach Curry	Indian	\N	2025-12-07 20:53:14.566347	1
631	Chicken and Pesto and Wild Mushroom Ragout	Comfort Food	\N	2025-12-07 20:53:14.566347	1
632	Spicy Ground Beef and Black Olive Tapenade Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
633	Pork and Pineapple and Onion Meatloaf	Comfort Food	\N	2025-12-07 20:53:14.566347	1
634	Beef and Bean and Corn Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
635	Chicken and Wild Rice and Roasted Red Pepper Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
636	Spicy Tofu and Zucchini Skewers	Vegetarian	\N	2025-12-07 20:53:14.566347	1
637	Chicken and Bacon and Tomato and Basil Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
638	Spicy Chicken and Feta and Spinach Stuffed Pitas	Mediterranean	\N	2025-12-07 20:53:14.566347	1
639	Pork and Apple and Cheddar Meatloaf	Comfort Food	\N	2025-12-07 20:53:14.566347	1
640	Beef and Potato and Carrot Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
641	Chicken and Sun-Dried Tomato and Pesto Sandwich (Main)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
642	Spicy Chickpea and Sweet Potato Stew with Dumplings	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
643	Chicken and Pesto and Artichoke Heart Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
644	Spicy Ground Turkey and Mushroom Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
645	Pork and Mushroom and Wild Rice Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
646	Beef and Cheese and Tomato Ragu with Polenta	Italian	\N	2025-12-07 20:53:14.566347	1
647	Chicken and Wild Rice and Broccoli Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
648	Spicy Tofu and Black Bean and Corn Salsa Bowl (Veg)	Mexican	\N	2025-12-07 20:53:14.566347	1
649	Chicken and Bacon and Onion Calzone	Italian	\N	2025-12-07 20:53:14.566347	1
650	Spicy Chicken and Apple and Brie Panini (Main)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
651	Pork and Pineapple and Green Bean Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
652	Beef and Potato and Leek Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
653	Chicken and Sun-Dried Tomato and Artichoke Heart Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
654	Spicy Chickpea and Roasted Vegetable Tart (Main)	Vegetarian	\N	2025-12-07 20:53:14.566347	1
655	Chicken and Pesto and Broccoli Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
656	Spicy Ground Beef and Black Bean Burrito	Mexican	\N	2025-12-07 20:53:14.566347	1
657	Pork and Mushroom and Spinach Calzone	Italian	\N	2025-12-07 20:53:14.566347	1
658	Beef and Cheese and Mushroom Risotto	Italian	\N	2025-12-07 20:53:14.566347	1
659	Chicken and Wild Rice and Corn Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
660	Spicy Tofu and Peanut Satay Salad (Main Size)	Asian	\N	2025-12-07 20:53:14.566347	1
661	Chicken and Bacon and Tomato and Basil Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
662	Spicy Chicken and Blackened Pork Chops	Pork	\N	2025-12-07 20:53:14.566347	1
663	Pork and Apple and Sage Stuffed Pork Loin	Pork	\N	2025-12-07 20:53:14.566347	1
664	Beef and Potato and Bacon Hash (Dinner)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
665	Chicken and Sun-Dried Tomato and Feta Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
666	Spicy Chickpea and Lentil Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
667	Chicken and Pesto and Wild Mushroom Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
668	Spicy Ground Turkey and Artichoke Dip Pasta (Main)	Italian	\N	2025-12-07 20:53:14.566347	1
669	Pork and Mushroom and Zucchini Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
670	Beef and Cheese and Potato Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
671	Chicken and Wild Rice and Celery Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
672	Spicy Tofu and Black Bean and Corn Fritters (Main Dish)	Mexican	\N	2025-12-07 20:53:14.566347	1
673	Chicken and Bacon and Avocado Quiche (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
674	Spicy Chicken and Roasted Root Vegetable Medley (Main)	Poultry	\N	2025-12-07 20:53:14.566347	1
675	Pork and Pineapple and Cabbage Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
676	Beef and Potato and Cheese Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
677	Chicken and Sun-Dried Tomato and Spinach Pasta Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
678	Spicy Chickpea and Roasted Red Pepper Hummus Wrap (Main)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
679	Chicken and Pesto and Artichoke Heart Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
680	Spicy Ground Beef and Black Bean Chili Mac	Comfort Food	\N	2025-12-07 20:53:14.566347	1
681	Pork and Mushroom and Swiss Cheese Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
682	Beef and Cheese and Broccoli Quiche (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
683	Chicken and Wild Rice and Red Pepper Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
684	Spicy Tofu and Vegetable Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
685	Chicken and Bacon and Tomato and Basil Calzone	Italian	\N	2025-12-07 20:53:14.566347	1
686	Spicy Chicken and Sun-Dried Tomato Pesto Sandwich (Main)	Sandwich/Burger	\N	2025-12-07 20:53:14.566347	1
687	Pork and Apple and Onion Stuffing Meatloaf	Comfort Food	\N	2025-12-07 20:53:14.566347	1
688	Beef and Potato and Onion Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
689	Chicken and Sun-Dried Tomato and Black Olive Tapenade Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
690	Spicy Chickpea and Sweet Potato Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
691	Chicken and Pesto and Feta Stuffed Chicken Breast	Italian	\N	2025-12-07 20:53:14.566347	1
692	Spicy Ground Turkey and Broccoli Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
693	Pork and Mushroom and Wild Rice Bake	Comfort Food	\N	2025-12-07 20:53:14.566347	1
694	Beef and Cheese and Mushroom Wellington	Meat	\N	2025-12-07 20:53:14.566347	1
695	Chicken and Wild Rice and Tomato Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
696	Spicy Tofu and Roasted Root Vegetable Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
697	Chicken and Bacon and Mushroom and Spinach Quiche (Main)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
698	Spicy Chicken and Zucchini and Tomato Skillet	Poultry	\N	2025-12-07 20:53:14.566347	1
699	Pork and Pineapple and Ham Calzone	Italian	\N	2025-12-07 20:53:14.566347	1
700	Beef and Potato and Mushroom Gratin (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
701	Chicken and Sun-Dried Tomato and Artichoke Heart Dip Pasta (Main)	Italian	\N	2025-12-07 20:53:14.566347	1
702	Spicy Chickpea and Vegetable Rice Bowl	Vegetarian	\N	2025-12-07 20:53:14.566347	1
703	Chicken and Pesto and Roasted Red Pepper Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
704	Spicy Ground Beef and Black Bean and Corn Enchiladas	Mexican	\N	2025-12-07 20:53:14.566347	1
705	Pork and Mushroom and Leek Gratin (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
706	Beef and Cheese and Potato Casserole with Bacon	Comfort Food	\N	2025-12-07 20:53:14.566347	1
707	Chicken and Wild Rice and Butternut Squash Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
708	Spicy Tofu and Black Bean and Corn Burrito	Mexican	\N	2025-12-07 20:53:14.566347	1
709	Chicken and Bacon and Tomato and Basil Stromboli	Italian	\N	2025-12-07 20:53:14.566347	1
710	Spicy Chicken and Apple and Brie Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
711	Pork and Pineapple and Ham Pizza (Gourmet)	Italian	\N	2025-12-07 20:53:14.566347	1
712	Beef and Potato and Onion Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
713	Chicken and Sun-Dried Tomato and Spinach and Feta Tart (Main)	Italian	\N	2025-12-07 20:53:14.566347	1
714	Spicy Chickpea and Roasted Vegetable Curry	Indian	\N	2025-12-07 20:53:14.566347	1
715	Chicken and Pesto and Broccoli Quiche (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
716	Spicy Ground Turkey and Mushroom Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
717	Pork and Mushroom and Zucchini Boat (Stuffed)	Pork	\N	2025-12-07 20:53:14.566347	1
718	Beef and Cheese and Mushroom and Spinach Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
720	Spicy Tofu and Black Eyed Peas and Rice (Dinner)	Vegetarian	\N	2025-12-07 20:53:14.566347	1
721	Chicken and Bacon and Tomato and Basil Stuffed Shells	Italian	\N	2025-12-07 20:53:14.566347	1
722	Spicy Chicken and Roasted Vegetable Tart (Main)	Poultry	\N	2025-12-07 20:53:14.566347	1
723	Pork and Pineapple and Pepper Calzone	Italian	\N	2025-12-07 20:53:14.566347	1
724	Beef and Potato and Carrot and Onion Stew	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
725	Chicken and Sun-Dried Tomato and Artichoke Heart Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
726	Spicy Chickpea and Vegetable Skewers	Vegetarian	\N	2025-12-07 20:53:14.566347	1
727	Chicken and Pesto and Feta Stuffed Peppers	Italian	\N	2025-12-07 20:53:14.566347	1
728	Spicy Ground Beef and Black Olive Tapenade Pasta Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
729	Pork and Mushroom and Wild Rice Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
730	Beef and Cheese and Potato Pancakes (Dinner)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
731	Chicken and Wild Rice and Red Pepper Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
732	Spicy Tofu and Black Bean and Corn Casserole	Mexican	\N	2025-12-07 20:53:14.566347	1
733	Chicken and Bacon and Onion and Cheese Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
734	Spicy Chicken and Sun-Dried Tomato and Feta Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
735	Pork and Pineapple and Ham and Pepperoni Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
736	Beef and Potato and Leek Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
737	Chicken and Sun-Dried Tomato and Spinach and Ricotta Cannelloni	Italian	\N	2025-12-07 20:53:14.566347	1
738	Spicy Chickpea and Sweet Potato and Kale Curry	Indian	\N	2025-12-07 20:53:14.566347	1
739	Chicken and Pesto and Wild Mushroom Quiche (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
740	Spicy Ground Turkey and Zucchini Skillet	Comfort Food	\N	2025-12-07 20:53:14.566347	1
741	Pork and Mushroom and Swiss Cheese Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
742	Beef and Cheese and Broccoli and Rice Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
743	Chicken and Wild Rice and Tomato Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
744	Spicy Tofu and Roasted Corn Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
745	Chicken and Bacon and Mushroom and Onion Gravy with Mash	Comfort Food	\N	2025-12-07 20:53:14.566347	1
746	Spicy Chicken and Black Bean Chili Mac and Cheese	Comfort Food	\N	2025-12-07 20:53:14.566347	1
747	Pork and Pineapple and Red Pepper Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
748	Beef and Potato and Mushroom and Cheese Pie	Comfort Food	\N	2025-12-07 20:53:14.566347	1
749	Chicken and Sun-Dried Tomato and Artichoke Heart Pasta Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
750	Spicy Chickpea and Vegetable Tagine with Couscous	African	\N	2025-12-07 20:53:14.566347	1
751	Chicken and Pesto and Broccoli and Cheese Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
752	Spicy Ground Beef and Black Bean and Corn Burrito Bowl	Mexican	\N	2025-12-07 20:53:14.566347	1
753	Pork and Mushroom and Zucchini Frittata (Main Dish)	Pork	\N	2025-12-07 20:53:14.566347	1
754	Beef and Cheese and Potato and Leek Gratin (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
756	Spicy Tofu and Black Bean and Corn Enchiladas Casserole	Mexican	\N	2025-12-07 20:53:14.566347	1
757	Chicken and Bacon and Tomato and Basil and Cheese Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
758	Spicy Chicken and Sun-Dried Tomato and Feta Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
759	Pork and Pineapple and Ham and Mushroom Pizza	Italian	\N	2025-12-07 20:53:14.566347	1
760	Beef and Potato and Onion and Cheese Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
761	Chicken and Sun-Dried Tomato and Spinach and Mushroom Lasagna	Italian	\N	2025-12-07 20:53:14.566347	1
762	Spicy Chickpea and Roasted Red Pepper and Spinach Curry	Indian	\N	2025-12-07 20:53:14.566347	1
763	Chicken and Pesto and Wild Mushroom and Spinach Quiche (Main)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
764	Spicy Ground Turkey and Artichoke Heart Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
765	Pork and Mushroom and Wild Rice and Broccoli Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
766	Beef and Cheese and Potato and Carrot Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
767	Chicken and Wild Rice and Red Pepper and Onion Skewers	Poultry	\N	2025-12-07 20:53:14.566347	1
768	Spicy Tofu and Black Bean and Corn Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
769	Chicken and Bacon and Mushroom and Spinach Alfredo	Italian	\N	2025-12-07 20:53:14.566347	1
770	Spicy Chicken and Zucchini and Tomato and Basil Pasta	Italian	\N	2025-12-07 20:53:14.566347	1
771	Pork and Pineapple and Red Pepper and Onion Stir Fry	Asian	\N	2025-12-07 20:53:14.566347	1
772	Beef and Potato and Leek and Carrot Stew	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
773	Chicken and Sun-Dried Tomato and Artichoke Heart Dip Casserole	Comfort Food	\N	2025-12-07 20:53:14.566347	1
774	Spicy Chickpea and Vegetable Curry with Coconut Milk	Indian	\N	2025-12-07 20:53:14.566347	1
775	Chicken and Pesto and Broccoli and Tomato Flatbread	Italian	\N	2025-12-07 20:53:14.566347	1
776	Spicy Ground Beef and Black Bean and Corn Stuffed Peppers	Mexican	\N	2025-12-07 20:53:14.566347	1
777	Pork and Mushroom and Zucchini Boat (Stuffed) with Cheese	Pork	\N	2025-12-07 20:53:14.566347	1
778	Beef and Cheese and Mushroom and Spinach Quiche (Main Dish)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
779	Chicken and Wild Rice and Tomato and Basil Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
780	Spicy Tofu and Roasted Corn and Black Bean Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
781	Chicken and Bacon and Tomato and Basil and Feta Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
782	Spicy Chicken and Sun-Dried Tomato and Artichoke Pasta Salad (Main Size)	Salad	\N	2025-12-07 20:53:14.566347	1
783	Pork and Pineapple and Ham and Mushroom Calzone	Italian	\N	2025-12-07 20:53:14.566347	1
784	Beef and Potato and Onion and Cheese and Bacon Soup (Hearty Main)	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
785	Chicken and Sun-Dried Tomato and Spinach and Ricotta Cannelloni Bake	Italian	\N	2025-12-07 20:53:14.566347	1
786	Spicy Chickpea and Sweet Potato and Kale Stew	Soup/Stew	\N	2025-12-07 20:53:14.566347	1
787	Chicken and Pesto and Wild Mushroom and Spinach and Feta Quiche (Main)	Comfort Food	\N	2025-12-07 20:53:14.566347	1
1	Authentic Pad Thai (Chicken/Tofu)	Asian	2025-12-07 20:55:37.828567	2025-12-07 20:53:14.566347	1
3	Shepherd's Pie (Beef/Lamb)	Comfort Food	2025-12-07 20:55:37.828567	2025-12-07 20:53:14.566347	1
4	Chicken Tikka Masala	Indian	2025-12-07 20:55:37.828567	2025-12-07 20:53:14.566347	1
5	Beef Stir Fry	Asian	2025-12-07 20:55:37.828567	2025-12-07 20:53:14.566347	1
112	Vegetarian Chili with Cornbread Topping	Soup/Stew	2025-12-07 20:57:09.282756	2025-12-07 20:53:14.566347	1
166	Spicy Korean Tofu Stew (Sundubu Jjigae)	Soup/Stew	2025-12-07 20:57:09.282756	2025-12-07 20:53:14.566347	1
343	Beef and Roasted Vegetable Bowl	Meat	2025-12-07 20:57:09.282756	2025-12-07 20:53:14.566347	1
403	Chicken and Roasted Red Pepper Hummus Wrap (Main)	Sandwich/Burger	2025-12-07 20:57:09.282756	2025-12-07 20:53:14.566347	1
430	Beef and Onion Soup (Hearty Main)	Soup/Stew	2025-12-07 20:57:09.282756	2025-12-07 20:53:14.566347	1
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: dinneruser
--

COPY public.users (id, email, password_hash, full_name, created_at) FROM stdin;
1	admin@dinnerflow.com	temp_hash_placeholder	Admin User	2025-12-09 01:46:33.839122
\.


--
-- Name: cooking_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dinneruser
--

SELECT pg_catalog.setval('public.cooking_log_id_seq', 1, false);


--
-- Name: recipes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dinneruser
--

SELECT pg_catalog.setval('public.recipes_id_seq', 2, true);


--
-- Name: search_terms_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dinneruser
--

SELECT pg_catalog.setval('public.search_terms_id_seq', 787, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dinneruser
--

SELECT pg_catalog.setval('public.users_id_seq', 5, true);


--
-- Name: cooking_log cooking_log_pkey; Type: CONSTRAINT; Schema: public; Owner: dinneruser
--

ALTER TABLE ONLY public.cooking_log
    ADD CONSTRAINT cooking_log_pkey PRIMARY KEY (id);


--
-- Name: recipes recipes_pkey; Type: CONSTRAINT; Schema: public; Owner: dinneruser
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_pkey PRIMARY KEY (id);


--
-- Name: search_terms search_terms_pkey; Type: CONSTRAINT; Schema: public; Owner: dinneruser
--

ALTER TABLE ONLY public.search_terms
    ADD CONSTRAINT search_terms_pkey PRIMARY KEY (id);


--
-- Name: search_terms search_terms_term_key; Type: CONSTRAINT; Schema: public; Owner: dinneruser
--

ALTER TABLE ONLY public.search_terms
    ADD CONSTRAINT search_terms_term_key UNIQUE (term);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: dinneruser
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: dinneruser
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: cooking_log cooking_log_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dinneruser
--

ALTER TABLE ONLY public.cooking_log
    ADD CONSTRAINT cooking_log_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id);


--
-- Name: recipes fk_recipes_user; Type: FK CONSTRAINT; Schema: public; Owner: dinneruser
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT fk_recipes_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: search_terms fk_search_terms_user; Type: FK CONSTRAINT; Schema: public; Owner: dinneruser
--

ALTER TABLE ONLY public.search_terms
    ADD CONSTRAINT fk_search_terms_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict HKLhj2WAmpfTplKtjlzHxdZyrF8HmEnEg5BJv6AbXBuc9IlDAsVqvGGVDF1LNei

