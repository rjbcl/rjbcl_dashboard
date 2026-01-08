from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.security import HTTPBearer
from database import get_mssql_conn
from pydantic import BaseModel, Field
import pyodbc

security = HTTPBearer()

router = APIRouter(tags=["MSSQL"])

# ------------------ MODELS ---------------------

class PolicyOut(BaseModel):
    PolicyNo: str
    FirstName: str
    LastName: str
    DOB: str
    Mobile: str | None = None
    BranchCode: int | None = None  
    BranchName: str | None = None


class RegistrationRequest(BaseModel):
    policy_no: str = Field(..., example="POL001")
    dob: str = Field(..., example="1990-01-15")


class ValidationResponse(BaseModel):
    allowed: bool
    message: str
    data: PolicyOut


# ---------------- ROUTES ------------------------

@router.get("/policies")
def get_policies(request: Request):
    user = getattr(request.state, "user", None)

    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()

        cursor.execute("""
                SELECT
                    tid.policyno,
                    tid.firstname,
                    tid.lastname,
                    tid.dob,
                    tid.mobile,
                    tid.branch AS branch_code,
                    tb.BranchName AS branch_name
                FROM tblInsureddetail tid
                LEFT JOIN tblBranch tb
                    ON tid.Branch = tb.Branch
            """)


        rows = cursor.fetchall()

        result = [
            {
                "PolicyNo": r.policyno,
                "FirstName": r.firstname,
                "LastName": r.lastname,
                "DOB": str(r.dob),
                "Mobile": r.mobile,
                "BranchCode": r.branch_code,
                "BranchName": r.branch_name,
            }
            for r in rows
        ]

        return {"user": user, "policies": result}

    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.get("/newpolicies", response_model=list[PolicyOut])
def get_policy_details(
    request: Request,
    policy_no: str = Query(...),
    dob: str = Query(...)
):
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                tid.policyno,
                tid.firstname,
                tid.lastname,
                tid.dob,
                tid.mobile,
                tid.branch AS branch_code,
                tb.BranchName AS branch_name
            FROM tblInsureddetail tid
            LEFT JOIN tblBranch tb
                ON tid.Branch = tb.Branch
            WHERE tid.policyno = ? AND tid.dob = ?
        """, (policy_no, dob))

        rows = cursor.fetchall()

    except pyodbc.Error as err:
        raise HTTPException(500, f"Database error: {str(err)}")

    finally:
        cursor.close()
        conn.close()

    if not rows:
        raise HTTPException(404, "No policy found")

    return [
        PolicyOut(
            PolicyNo=r.policyno,
            FirstName=r.firstname,
            LastName=r.lastname,
            DOB=str(r.dob),
            Mobile=r.mobile,
            BranchCode=r.branch_code,
            BranchName=r.branch_name,
        )
        for r in rows
    ]


@router.post("/validate-registration", response_model=ValidationResponse)
def validate_registration(data: RegistrationRequest):
    policy_no = data.policy_no
    dob = data.dob

    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()

        cursor.execute("""
           SELECT
                tid.policyno,
                tid.firstname,
                tid.lastname,
                tid.dob,
                tid.mobile,
                tid.branch AS branch_code,
                tb.BranchName AS branch_name
            FROM tblInsureddetail tid
            LEFT JOIN tblBranch tb
                ON tid.Branch = tb.Branch
            WHERE tid.policyno = ? AND tid.dob = ?

        """, (policy_no, dob))

        row = cursor.fetchone()

    except pyodbc.Error as err:
        raise HTTPException(500, f"Query failed: {str(err)}")

    finally:
        cursor.close()
        conn.close()

    if not row:
        raise HTTPException(404, "Invalid Policy Number or DOB")

    return ValidationResponse(
    allowed=True,
    message="Valid for registration",
    data=PolicyOut(
        PolicyNo=row.policyno,
        FirstName=row.firstname,
        LastName=row.lastname,
        DOB=str(row.dob),
        Mobile=row.mobile,
        BranchCode=row.branch_code,
        BranchName=row.branch_name,
    )
)

@router.get("/related-policies")
def related_policies(
    firstname: str,
    lastname: str,
    dob: str,
    mobile: str
):
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT policyno
            FROM tblInsureddetail
            WHERE firstname = ? 
              AND lastname = ?
              AND dob = ?
              AND mobile = ?
        """, (firstname, lastname, dob, mobile))

        rows = cursor.fetchall()
        return [r.policyno for r in rows]

    except Exception as e:
        raise HTTPException(500, f"DB error: {str(e)}")
    finally:
        cursor.close()
        conn.close()
