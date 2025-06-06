CREATE TABLE tournaments (
    tournament_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_title TEXT,
    description TEXT,
    wallet_address TEXT,
    thumbnail TEXT,
    contract_address Text
);

CREATE TABLE candidates (
    candidate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER,
    candidate_name TEXT,
    image_url TEXT,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id)
);
