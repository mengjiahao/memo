/* protocol define using rpcgen */ 

struct pingrequest {
    opaque clientId<>;
};

struct pingresponse {
    int output;
};

struct hashrequest {
    opaque clientId<>;
    int isFinished;
    opaque textin<>;
    int part;
    int hash;
    int hasParts;
    int filesize;
};

struct hashresponse {
    int hash;
};

program PROG {
    version PROG_VER_1 {
        pingresponse PINGPROG(pingrequest) = 1;
        hashresponse HASHPROG(hashrequest) = 2;
    } = 1;
} = 0x77777777;