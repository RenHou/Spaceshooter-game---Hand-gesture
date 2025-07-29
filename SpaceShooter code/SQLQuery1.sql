use LeaderboardSpaceShooter;

CREATE DATABASE LeaderboardSpaceShooter; 

CREATE TABLE Leaderboard(
	username VARCHAR(100),
	score INT,
	saveTime BIGINT
);

INSERT INTO Leaderboard VALUES 
('abu',200,1747108100),
('ali',1000,1747108000), 
('az',122312,1747107732),
('dan',123132,1747107634),
('mai',231232,1747107312),
('ren',100000,1747107508),
('wei',123233,1747107592),
('xuan',213223,1747107900);
