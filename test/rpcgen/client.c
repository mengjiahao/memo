#include <arpa/inet.h>
#include <netinet/in.h>
#include <netdb.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/time.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sysexits.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <wordexp.h>
#include <rpc/rpc.h>
#include "proto.h" // generated by rpcgen

int debug = 0;
CLIENT *clnt;

void usage(char *program_name) {
	printf("Usage: %s [-d] -s <server>\n", program_name);
}

void f_ping(){
	if (debug)
		printf("PING\n");
        
        struct sockaddr_in addr;
        get_myaddress(&addr);
        
        char *reqstr = malloc(sizeof(char)*50);
        char *addrstr = inet_ntoa(addr.sin_addr);
        sprintf(reqstr,"%s:%d",addrstr,addr.sin_port);

        pingrequest request;
        request.clientId.clientId_val = reqstr;
        request.clientId.clientId_len = strlen(reqstr);

        struct timeval start;
        struct timeval end;
        int rc1, rc2;
        rc1 = gettimeofday(&start, NULL); //Get current time

        pingresponse pres;
        pres.output = 0x66666666;
        pingprog_1(&request, &pres, clnt);
        
        rc2 = gettimeofday(&end, NULL); //Get current time
        printf("%ld.%ld s\n", (end.tv_sec - start.tv_sec)/2, (end.tv_usec - start.tv_usec)/2); //Print time interval
}

void f_hash(char *src){
	if (debug)
		printf("HASH <SRC=%s>\n", src);
	
        //////////// Add IP to struct ///////////////////////////
        struct sockaddr_in addr;
        get_myaddress(&addr);

        char *reqstr = malloc(sizeof(char)*50);
        char *addrstr = inet_ntoa(addr.sin_addr);
        sprintf(reqstr,"%s:%d",addrstr,addr.sin_port);

        //Open file //////////////////
        char *readbuf= (char *)malloc(sizeof(char)*1028);
        FILE *fd1 = fopen(src, "r");
        if(fd1 == NULL) perror("fopen");

        //Obtain size /////////////////
        int file_size = 0;
        fseek(fd1, 0, SEEK_END);
        file_size = ftell (fd1);
        rewind (fd1);

        //Hash //////////////////
        int readchars = 0;
        int written = 0;
        int hash = 0;
        int i = 0;
        int hasParts = (file_size < 1024) ? 0 : 1;

        while (file_size > 0) {
             i++;
             readchars = sizeof(char) * 1024;
             if (file_size < readchars) readchars = file_size;  //If there are less than 500 to EOF, read that number///
             if (readchars < 0) readchars = 1024 + readchars;    ////////////////////////////////////////////////////////
             file_size -= readchars; //Decrement chars left to read
             fseek(fd1, written, SEEK_SET);
             fread(readbuf, 1, readchars, fd1);

             written += readchars;

             struct hashrequest request;
             request.clientId.clientId_val = reqstr;
             request.clientId.clientId_len = strlen(reqstr);
             request.textin.textin_val = readbuf;
             request.textin.textin_len = readchars;
             request.isFinished = (readchars < 1024) ? 1 : 0;
             request.part = i;
             if (request.isFinished == 1) request.hash = hash;
             request.hash = hash;
             request.hasParts = hasParts;
             request.filesize = readchars;
             
             struct hashresponse response;
             hashprog_1(&request, &response, clnt);

             hash = response.hash;
             //printf("%d\n",hash);
             //printf("hashAcum %d\n",hash);
        }
        printf("%d\n",hash);
        free(reqstr);
        fclose(fd1);

	// Write code here
}

void shell() {
	char line[1024];
	char *pch;
	int exit = 0;
	
	wordexp_t p;
	char **w;
	int ret;
	
	memset(&p, 0, sizeof(wordexp));
	do {
		fprintf(stdout, "c> ");
		memset(line, 0, 1024);
		pch = fgets(line, 1024, stdin);
		
		if ((strlen(line)>1) && ((line[strlen(line)-1]=='\n') || (line[strlen(line)-1]=='\r')))
			line[strlen(line)-1]='\0';
		
		ret = wordexp((const char *)line, &p, 0);
		if (ret == 0) {
			w = p.we_wordv;
			if ((w != NULL) && (p.we_wordc > 0)) {
				if (strcmp(w[0],"ping")==0) {
					if (p.we_wordc == 1)
						f_ping();
					else
						printf("Syntax error. Use: ping\n");
				} else if (strcmp(w[0], "hash")==0) {
					if (p.we_wordc == 2)
						f_hash(w[1]);
					else
						printf("Syntax error. Use: hash <source_file>\n");
				} else {
					fprintf(stderr, "Error: command '%s' not valid.\n", w[0]);
				}
			}
			wordfree(&p);
		}
	} while ((pch != NULL) && (!exit));
}


int main(int argc, char *argv[]) {
    char *program_name = argv[0];
    int opt = 0;
    char *server = NULL;
    setbuf(stdout, NULL);

    while (-1 != (opt = getopt(argc, argv, "ds:"))) {  // getopt defined in <unistd.h>
        switch (opt) {
          case 'd':
            debug = 1;
            break;
          case 's':
            server = optarg;
            break;
          default:
            usage(program_name);
            exit(EX_USAGE);  // EX_USAGE is defined in <sysexits.h>
        }
    }

    if (debug)
		printf("SERVER: %s\n", server);
	
	char *host;
    char *expparam = "-s";
    int valid = strcmp(argv[1], expparam);
    if(argc != 3 || valid != 0) {
        usage(argv[0]);
        exit(1);
	}

	host = argv[2];  // Get host from parameters
    //////////// Create tcp connection with host ////////////////////////
    if ((clnt = clnt_create(host, PROG, PROG_VER_1, "tcp")) == NULL) {
        printf("Error connecting to %s\n",host);
        clnt_pcreateerror(host);
        exit(1);
    }

	shell();
	
	exit(EXIT_SUCCESS);
}