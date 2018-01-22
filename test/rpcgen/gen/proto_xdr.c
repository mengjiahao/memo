/*
 * Please do not edit this file.
 * It was generated using rpcgen.
 */

#include "proto.h"

bool_t
xdr_pingrequest (XDR *xdrs, pingrequest *objp)
{
	register int32_t *buf;

	 if (!xdr_bytes (xdrs, (char **)&objp->clientId.clientId_val, (u_int *) &objp->clientId.clientId_len, ~0))
		 return FALSE;
	return TRUE;
}

bool_t
xdr_pingresponse (XDR *xdrs, pingresponse *objp)
{
	register int32_t *buf;

	 if (!xdr_int (xdrs, &objp->output))
		 return FALSE;
	return TRUE;
}

bool_t
xdr_hashrequest (XDR *xdrs, hashrequest *objp)
{
	register int32_t *buf;


	if (xdrs->x_op == XDR_ENCODE) {
		 if (!xdr_bytes (xdrs, (char **)&objp->clientId.clientId_val, (u_int *) &objp->clientId.clientId_len, ~0))
			 return FALSE;
		 if (!xdr_int (xdrs, &objp->isFinished))
			 return FALSE;
		 if (!xdr_bytes (xdrs, (char **)&objp->textin.textin_val, (u_int *) &objp->textin.textin_len, ~0))
			 return FALSE;
		buf = XDR_INLINE (xdrs, 4 * BYTES_PER_XDR_UNIT);
		if (buf == NULL) {
			 if (!xdr_int (xdrs, &objp->part))
				 return FALSE;
			 if (!xdr_int (xdrs, &objp->hash))
				 return FALSE;
			 if (!xdr_int (xdrs, &objp->hasParts))
				 return FALSE;
			 if (!xdr_int (xdrs, &objp->filesize))
				 return FALSE;
		} else {
			IXDR_PUT_LONG(buf, objp->part);
			IXDR_PUT_LONG(buf, objp->hash);
			IXDR_PUT_LONG(buf, objp->hasParts);
			IXDR_PUT_LONG(buf, objp->filesize);
		}
		return TRUE;
	} else if (xdrs->x_op == XDR_DECODE) {
		 if (!xdr_bytes (xdrs, (char **)&objp->clientId.clientId_val, (u_int *) &objp->clientId.clientId_len, ~0))
			 return FALSE;
		 if (!xdr_int (xdrs, &objp->isFinished))
			 return FALSE;
		 if (!xdr_bytes (xdrs, (char **)&objp->textin.textin_val, (u_int *) &objp->textin.textin_len, ~0))
			 return FALSE;
		buf = XDR_INLINE (xdrs, 4 * BYTES_PER_XDR_UNIT);
		if (buf == NULL) {
			 if (!xdr_int (xdrs, &objp->part))
				 return FALSE;
			 if (!xdr_int (xdrs, &objp->hash))
				 return FALSE;
			 if (!xdr_int (xdrs, &objp->hasParts))
				 return FALSE;
			 if (!xdr_int (xdrs, &objp->filesize))
				 return FALSE;
		} else {
			objp->part = IXDR_GET_LONG(buf);
			objp->hash = IXDR_GET_LONG(buf);
			objp->hasParts = IXDR_GET_LONG(buf);
			objp->filesize = IXDR_GET_LONG(buf);
		}
	 return TRUE;
	}

	 if (!xdr_bytes (xdrs, (char **)&objp->clientId.clientId_val, (u_int *) &objp->clientId.clientId_len, ~0))
		 return FALSE;
	 if (!xdr_int (xdrs, &objp->isFinished))
		 return FALSE;
	 if (!xdr_bytes (xdrs, (char **)&objp->textin.textin_val, (u_int *) &objp->textin.textin_len, ~0))
		 return FALSE;
	 if (!xdr_int (xdrs, &objp->part))
		 return FALSE;
	 if (!xdr_int (xdrs, &objp->hash))
		 return FALSE;
	 if (!xdr_int (xdrs, &objp->hasParts))
		 return FALSE;
	 if (!xdr_int (xdrs, &objp->filesize))
		 return FALSE;
	return TRUE;
}

bool_t
xdr_hashresponse (XDR *xdrs, hashresponse *objp)
{
	register int32_t *buf;

	 if (!xdr_int (xdrs, &objp->hash))
		 return FALSE;
	return TRUE;
}