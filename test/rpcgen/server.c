
#include <arpa/inet.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <rpc/rpc.h>
#include <unistd.h>
#include "proto.h" /* Created by rpcgen */

struct auxstat{
    int pingnum;
    int swapnum;
    int hashnum;
    int checknum;
    int statnum;
} ;

struct auxstat st;

bool_t pingprog_1_svc(pingrequest *request, pingresponse *response, struct svc_req *rqstp)
{
    st.pingnum++;
    char *clieAddr = request->clientId.clientId_val;
    printf("s> %s ping\n", clieAddr);

    response->output =  0;
    return (TRUE);
}

bool_t hashprog_1_svc(hashrequest *request, hashresponse *response, struct svc_req *rqstp)
{
    char *buffer = request->textin.textin_val;

    int currentHash = 0;
    if (request->part == 1) printf("s> %s init hash %d\n", request->clientId.clientId_val, request->filesize);
    
    /////////////// OBTAIN PART HASH ///////////////////////////////////////////
    int i = 0;
    for (i = 0; i < request->textin.textin_len; i++) {
        currentHash = (currentHash + buffer[i])%1000000000;
    }

    //////////////// OBTAIN FULL HASH ///////////////////////////////////////////
    if (currentHash<0) currentHash += 1000000000;//Normalize hash value
    currentHash = (currentHash + request->hash)%1000000000; //Obtain hash with previous chunks
    if (currentHash<0) currentHash += 1000000000;//Normalize hash value

    response->hash = currentHash; //Assign output

    if (request->isFinished == 1) {
        st.hashnum++;
        printf("s> %s hash = %d\n", request->clientId.clientId_val, currentHash);
    }
    return (TRUE);
}


int prog_1_freeresult (SVCXPRT *arg0, xdrproc_t arg1, caddr_t arg2){

    //xdr_free(arg1, arg2);
    return TRUE; //1
}