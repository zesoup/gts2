CREATE TYPE ENTITY AS ENUM ('target','car','pedestrian','track','bullet','other', 'wreck');                                                                 
-- wreck, blood, track to decials

CREATE TYPE _typ AS ENUM ('bloody','died','spawned','left','joined','hit','shot','message','isalive','boosts');



create type _inertia as(
       x real,
       y real
       );
