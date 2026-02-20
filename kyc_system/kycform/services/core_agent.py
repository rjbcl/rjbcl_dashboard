from django.db import connections
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def verify_agent_from_core(agent_code: str, dob: str) -> bool:
    """
    Verify agent against CORE (SQL Server) using proc_Online_AgentLogin.

    Rules:
    - DOB is used as password (YYYYMMDD)
    - Procedure does NOT return rows
    - Successful execution = VERIFIED
    - Any exception = FAILED
    """

    # -----------------------------
    # Input validation
    # -----------------------------
    if not agent_code or not dob:
        return False

    try:
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
    except ValueError:
        return False

    user_pwd = dob.replace("-", "")  # YYYYMMDD

    # -----------------------------
    # CORE CALL (AUTHORITATIVE)
    # -----------------------------
    try:
        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(
                """
                EXEC proc_Online_AgentLogin
                    @Flag     = %s,
                    @PolicyNo = NULL,
                    @DOB      = %s,
                    @UserPwd  = %s,
                    @UserName = %s,
                    @Token    = NULL
                """,
                [
                    "LOGIN",        # @Flag
                    dob_date,       # @DOB
                    user_pwd,       # @UserPwd
                    agent_code,     # @UserName (AgentCode)
                ]
            )

        # ✅ NO exception = VERIFIED
        return True

    except Exception as e:
        logger.warning(
            "CORE agent verification failed | agent_code=%s | error=%s",
            agent_code,
            str(e)
        )
        return False
