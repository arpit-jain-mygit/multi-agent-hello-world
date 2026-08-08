-- Very basic single-column table for the postgres_tool_agents.py example.
CREATE TABLE IF NOT EXISTS hello_messages (
    message TEXT
);

INSERT INTO hello_messages (message) VALUES
    ('Hello World'),
    ('Hola Mundo'),
    ('Bonjour le monde');
