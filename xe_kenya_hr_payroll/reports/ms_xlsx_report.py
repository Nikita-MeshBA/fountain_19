from odoo import models


class MSXlsx(models.AbstractModel):
    _name = "report.xe_kenya_hr_payroll.ms_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "MS Report XLSX"

    def department_total(self, records):
        basic = 0
        house_allowance = 0
        other_earnings = 0
        overtime = 0
        tax_allowance = 0
        total_earnings = 0
        pension = 0
        pension_contribution = 0
        paye = 0
        nssf = 0
        nhif = 0
        insurance = 0
        advance = 0
        welfare_contribution = 0
        absa_loan_deduction = 0
        sacco_contribution = 0
        mwito_contribution = 0
        school_fees = 0
        long_term_adv_ded = 0
        net_salary = 0
        total_deductions = 0
        for line in records:
            basic = basic + line["basic"]
            house_allowance = house_allowance + line["house_allowance"]
            other_earnings = other_earnings + line["other_earnings"]
            overtime = overtime + line["overtime"]
            tax_allowance = tax_allowance + line["tax_allowance"]
            total_earnings = total_earnings + line["total_earnings"]
            pension = pension + line["pension"]
            pension_contribution = pension_contribution + line["pension_contribution"]
            paye = paye + line["paye"]
            nssf = nssf + line["nssf"]
            nhif = nhif + line["nhif"]
            insurance = insurance + line["insurance"]
            advance = advance + line["advance"]
            welfare_contribution = welfare_contribution + line["welfare_contribution"]
            absa_loan_deduction = absa_loan_deduction + line["absa_loan_deduction"]
            sacco_contribution = sacco_contribution + line["sacco_contribution"]
            mwito_contribution = mwito_contribution + line["mwito_contribution"]
            school_fees = school_fees + line["school_fees"]
            long_term_adv_ded = long_term_adv_ded + line["long_term_adv_ded"]
            net_salary = net_salary + line["net_salary"]
            total_deductions = total_deductions + line["total_deductions"]
        return {
            "basic": basic,
            "house_allowance": house_allowance,
            "other_earnings": other_earnings,
            "overtime": overtime,
            "tax_allowance": tax_allowance,
            "total_earnings": total_earnings,
            "pension": pension,
            "pension_contribution": pension_contribution,
            "paye": paye,
            "nssf": nssf,
            "nhif": nhif,
            "insurance": insurance,
            "advance": advance,
            "welfare_contribution": welfare_contribution,
            "absa_loan_deduction": absa_loan_deduction,
            "sacco_contribution": sacco_contribution,
            "mwito_contribution": mwito_contribution,
            "school_fees": school_fees,
            "long_term_adv_ded": long_term_adv_ded,
            "net_salary": net_salary,
            "total_deductions": total_deductions,
        }

    # Static Logic
    def generate_xlsx_report_custom_one(self, workbook, data, payslip):
        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("ms_report")
        sheet.write(0, 0, "STAFF NO", format1)
        sheet.write(0, 1, "NAME", format1)
        sheet.write(0, 2, "BASIC PAY", format1)
        sheet.write(0, 3, "HOUSE ALLOWANCE", format1)
        sheet.write(0, 4, "OTHER EARNINGS", format1)
        sheet.write(0, 5, "OVERTIME", format1)
        sheet.write(0, 6, "TAX ALLOWANCE", format1)
        sheet.write(0, 7, "TOTAL EARNINGS", format1)
        sheet.write(0, 8, "PENSION", format1)
        sheet.write(0, 9, "PENSION CONTRIBUTION", format1)
        sheet.write(0, 10, "PAYE", format1)
        sheet.write(0, 11, "NSSF", format1)
        sheet.write(0, 12, "NHIF", format1)
        sheet.write(0, 13, "INSURANCE", format1)
        sheet.write(0, 14, "ADVANCE", format1)
        sheet.write(0, 15, "WELFARE CONTRIBUTION", format1)
        sheet.write(0, 16, "ABSA LOAN", format1)
        sheet.write(0, 17, "BIBLIA SACCO", format1)
        sheet.write(0, 18, "MWITO SACCO WITO", format1)
        sheet.write(0, 19, "SCHOOL FEES", format1)
        sheet.write(0, 20, "LONG TERM ADVANCE", format1)
        sheet.write(0, 21, "TOTAL DEDUCTIONS", format1)
        sheet.write(0, 22, "NET", format1)
        sheet.set_column(0, 22, 20)
        result = data["form"]["payslip_data"]
        total_basic = 0
        total_house_allowance = 0

        total_other_earnings = 0
        total_overtime = 0
        total_tax_allowance = 0
        grand_total_earnings = 0
        total_pension = 0
        total_pension_contribution = 0
        total_paye = 0
        total_nssf = 0
        total_nhif = 0
        total_insurance = 0
        total_advance = 0
        total_welfare_contribution = 0
        total_absa_loan_deduction = 0
        total_sacco_contribution = 0
        total_mwito_contribution = 0
        total_school_fees = 0
        total_long_term_adv_ded = 0
        total_net_salary = 0
        grand_total_deductions = 0
        i = 0
        for rec in result:
            i = i + 1
            sheet.write(i, 0, "DEPARTMENT", format1)
            sheet.write(i, 1, rec["department_name"], format1)
            department_total = self.department_total(rec["line_ids"])
            department_basic_total = department_total["basic"]
            department_house_allowance_total = department_total["house_allowance"]
            department_other_earnings_total = department_total["other_earnings"]
            department_overtime_total = department_total["overtime"]
            department_tax_allowance_total = department_total["tax_allowance"]
            department_total_earnings = department_total["total_earnings"]
            department_total_pension = department_total["pension"]
            department_pension_contribution = department_total["pension_contribution"]

            department_total_paye = department_total["paye"]
            department_total_nssf = department_total["nssf"]
            department_nhif_total = department_total["nhif"]
            department_insurance_total = department_total["insurance"]
            department_advance_total = department_total["advance"]
            department_welfare_contribution_total = department_total[
                "welfare_contribution"
            ]
            department_absa_loan_deduction_total = department_total[
                "absa_loan_deduction"
            ]
            department_sacco_contribution_total = department_total["sacco_contribution"]
            department_mwito_contribution_total = department_total["mwito_contribution"]
            department_school_fees_total = department_total["school_fees"]
            department_long_term_adv_ded_total = department_total["long_term_adv_ded"]
            department_net_salary_total = department_total["net_salary"]
            department_total_deductions_total = department_total["total_deductions"]
            total_basic = total_basic + department_basic_total
            total_house_allowance = (
                total_house_allowance + department_house_allowance_total
            )
            total_other_earnings = (
                total_other_earnings + department_other_earnings_total
            )
            total_overtime = total_overtime + department_overtime_total
            total_tax_allowance = total_tax_allowance + department_tax_allowance_total
            grand_total_earnings = grand_total_earnings + department_total_earnings
            total_pension = total_pension + department_total_pension
            total_pension_contribution = (
                total_pension_contribution + department_pension_contribution
            )

            total_paye = total_paye + department_total_paye
            total_nssf = total_nssf + department_total_nssf
            total_nhif = total_nhif + department_nhif_total
            total_insurance = total_insurance + department_insurance_total
            total_advance = total_advance + department_advance_total
            total_welfare_contribution = (
                total_welfare_contribution + department_welfare_contribution_total
            )
            total_absa_loan_deduction = (
                total_absa_loan_deduction + department_absa_loan_deduction_total
            )
            total_sacco_contribution = (
                total_sacco_contribution + department_sacco_contribution_total
            )
            total_mwito_contribution = (
                total_mwito_contribution + department_mwito_contribution_total
            )
            total_school_fees = total_school_fees + department_school_fees_total
            total_long_term_adv_ded = (
                total_long_term_adv_ded + department_long_term_adv_ded_total
            )
            total_net_salary = total_net_salary + department_net_salary_total
            grand_total_deductions = (
                grand_total_deductions + department_total_deductions_total
            )

            department_no_employees = len(rec["line_ids"]) or 0
            for line in rec["line_ids"]:
                i = i + 1
                sheet.write(i, 0, line["staff_no"], format2)
                sheet.write(i, 1, line["employee"], format2)
                sheet.write(i, 2, line["basic"], format2)
                sheet.write(i, 3, line["house_allowance"], format2)
                sheet.write(i, 4, line["other_earnings"], format2)
                sheet.write(i, 5, line["overtime"], format2)
                sheet.write(i, 6, line["tax_allowance"], format2)
                sheet.write(i, 7, line["total_earnings"], format2)
                sheet.write(i, 8, line["pension"], format2)
                sheet.write(i, 9, line["pension_contribution"], format2)
                sheet.write(i, 10, line["paye"], format2)
                sheet.write(i, 11, line["nssf"], format2)
                sheet.write(i, 12, line["nhif"], format2)
                sheet.write(i, 13, line["insurance"], format2)
                sheet.write(i, 14, line["advance"], format2)
                sheet.write(i, 15, line["welfare_contribution"], format2)
                sheet.write(i, 16, line["absa_loan_deduction"], format2)
                sheet.write(i, 17, line["sacco_contribution"], format2)
                sheet.write(i, 18, line["mwito_contribution"], format2)
                sheet.write(i, 19, line["school_fees"], format2)
                sheet.write(i, 20, line["long_term_adv_ded"], format2)
                sheet.write(i, 21, line["total_deductions"], format2)
                sheet.write(i, 22, line["net_salary"], format2)
            i = i + 1
            string_1 = "DEPARTMENT " + "- " + rec["department_name"] + " -" + " TOTAL"
            sheet.write(i, 0, string_1, format1)
            sheet.write(i, 2, department_basic_total, format1)
            sheet.write(i, 3, department_house_allowance_total, format1)
            sheet.write(i, 4, department_other_earnings_total, format1)
            sheet.write(i, 5, department_overtime_total, format1)
            sheet.write(i, 6, department_tax_allowance_total, format1)
            sheet.write(i, 7, department_total_earnings, format1)
            sheet.write(i, 8, department_total_pension, format1)
            sheet.write(i, 9, department_pension_contribution, format1)

            sheet.write(i, 10, department_total_paye, format1)
            sheet.write(i, 11, department_total_nssf, format1)
            sheet.write(i, 12, department_nhif_total, format1)
            sheet.write(i, 13, department_insurance_total, format1)
            sheet.write(i, 14, department_advance_total, format1)
            sheet.write(i, 15, department_welfare_contribution_total, format1)
            sheet.write(i, 16, department_absa_loan_deduction_total, format1)
            sheet.write(i, 17, department_sacco_contribution_total, format1)
            sheet.write(i, 18, department_mwito_contribution_total, format1)
            sheet.write(i, 19, department_school_fees_total, format1)
            sheet.write(i, 20, department_long_term_adv_ded_total, format1)
            sheet.write(i, 21, department_total_deductions_total, format1)
            sheet.write(i, 22, department_net_salary_total, format1)
            i = i + 1
            string_2 = (
                "TOTAL NO OF EMPLOYEES IN DEPARTMENT "
                + "- "
                + rec["department_name"]
                + " - "
                + str(department_no_employees)
            )
            sheet.write(i, 0, string_2, format1)
        i = i + 1
        sheet.write(i, 0, "GRAND TOTAL", format1)
        sheet.write(i, 2, total_basic, format1)
        sheet.write(i, 3, total_house_allowance, format1)
        sheet.write(i, 4, total_other_earnings, format1)
        sheet.write(i, 5, total_overtime, format1)
        sheet.write(i, 6, total_tax_allowance, format1)
        sheet.write(i, 7, grand_total_earnings, format1)
        sheet.write(i, 8, total_pension, format1)
        sheet.write(i, 9, total_pension_contribution, format1)
        sheet.write(i, 10, total_paye, format1)
        sheet.write(i, 11, total_nssf, format1)
        sheet.write(i, 12, total_nhif, format1)
        sheet.write(i, 13, total_insurance, format1)
        sheet.write(i, 14, total_advance, format1)
        sheet.write(i, 15, total_welfare_contribution, format1)
        sheet.write(i, 16, total_absa_loan_deduction, format1)
        sheet.write(i, 17, total_sacco_contribution, format1)
        sheet.write(i, 18, total_mwito_contribution, format1)
        sheet.write(i, 19, total_school_fees, format1)
        sheet.write(i, 20, total_long_term_adv_ded, format1)
        sheet.write(i, 21, grand_total_deductions, format1)
        sheet.write(i, 22, total_net_salary, format1)

    # Dynamic Department calculation process
    def department_total_logic(self, records, header_rows):
        basic = 0
        house_allowance = 0
        other_earnings = 0
        overtime = 0
        tax_allowance = 0
        total_earnings = 0
        pension = 0
        pension_contribution = 0
        paye = 0
        nssf = 0
        nhif = 0
        insurance = 0
        advance = 0
        welfare_contribution = 0
        absa_loan_deduction = 0
        sacco_contribution = 0
        mwito_contribution = 0
        school_fees = 0
        long_term_adv_ded = 0
        net_salary = 0
        total_deductions = 0
        monthly_personal_relief = 0
        tax_charge = 0
        taxable_salary = 0
        transport_allowance = 0
        bonus = 0
        other_benefits = 0
        loan_amount = 0
        medical_deduction = 0
        long_term_advance = 0
        monthly_insurance_relief = 0
        gratuity_total = 0
        insurance_premium_deduction = 0
        helb_deduction = 0
        gratuity = 0
        test_rule = 0
        consolidated_benefits_support = 0
        kimisitu_sacco_contribution_deduction = 0
        finnlemm_sacco_contribution_deduction = 0
        other_deductions = 0
        parking_fee_deduction = 0
        for line in records:
            if line.get("basic_salary"):
                basic = basic + line["basic_salary"]

            if line.get("monthly_basic_salary"):
                basic = basic + line["monthly_basic_salary"]

            if line.get("house_allowance"):
                house_allowance = house_allowance + line["house_allowance"]

            if line.get("other_earnings"):
                other_earnings = other_earnings + line["other_earnings"]

            if line.get("overtime"):
                overtime = overtime + line["overtime"]

            if line.get("tax_allowance"):
                tax_allowance = tax_allowance + line["tax_allowance"]

            if line.get("total_earning"):
                total_earnings = total_earnings + line["total_earning"]

            if line.get("pension"):
                pension = pension + line["pension"]

            if line.get("pension_contribution_deduction"):
                pension_contribution = (
                    pension_contribution + line["pension_contribution_deduction"]
                )

            if line.get("paye"):
                paye = paye + line["paye"]

            if line.get("nssf"):
                nssf = nssf + line["nssf"]

            if line.get("nhif"):
                nhif = nhif + line["nhif"]

            if line.get("insurance"):
                insurance = insurance + line["insurance"]

            if line.get("monthly_insurance_relief"):
                monthly_insurance_relief = (
                    monthly_insurance_relief + line["monthly_insurance_relief"]
                )

            if line.get("advance"):
                advance = advance + line["advance"]

            if line.get("welfare_contribution"):
                welfare_contribution = (
                    welfare_contribution + line["welfare_contribution"]
                )

            if line.get("loan_deduction"):
                absa_loan_deduction = absa_loan_deduction + line["loan_deduction"]

            if line.get("biblio_sacco_contribution_deduction"):
                sacco_contribution = (
                    sacco_contribution + line["biblio_sacco_contribution_deduction"]
                )

            if line.get("mwito_sacco_contribution_deduction"):
                mwito_contribution = (
                    mwito_contribution + line["mwito_sacco_contribution_deduction"]
                )

            if line.get("school_fees"):
                school_fees = school_fees + line["school_fees"]

            if line.get("advance_deduction"):
                long_term_adv_ded = long_term_adv_ded + line["advance_deduction"]

            if line.get("net_salary"):
                net_salary = net_salary + line["net_salary"]

            if line.get("net_salary"):
                total_deductions = total_deductions + line["total_deductions"]

            if line.get("monthly_personal_relief"):
                monthly_personal_relief = (
                    monthly_personal_relief + line["monthly_personal_relief"]
                )

            if line.get("taxable_salary"):
                taxable_salary = taxable_salary + line["taxable_salary"]

            if line.get("tax_charged"):
                tax_charge = tax_charge + line["tax_charged"]

            if line.get("transport_allowance"):
                transport_allowance = transport_allowance + line["transport_allowance"]

            if line.get("bonus"):
                bonus = bonus + line["bonus"]

            if line.get("other_benefits"):
                other_benefits = other_benefits + line["other_benefits"]

            if line.get("loan_amount"):
                loan_amount = loan_amount + line["loan_amount"]

            if line.get("medical_deduction"):
                medical_deduction = medical_deduction + line["medical_deduction"]

            if line.get("long_term_advance"):
                long_term_advance = long_term_advance + line["long_term_advance"]

            if line.get("insurance_premium_deduction"):
                insurance_premium_deduction = (
                    insurance_premium_deduction + line["insurance_premium_deduction"]
                )
            if line.get("helb_deduction"):
                helb_deduction = helb_deduction + line["helb_deduction"]
            if line.get("test_rule"):
                test_rule = test_rule + line["test_rule"]
            if line.get("gratuity_total"):
                gratuity_total = gratuity_total + line["gratuity_total"]
            if line.get("gratuity"):
                gratuity = gratuity + line["gratuity"]
            if line.get("other_deductions"):
                other_deductions = other_deductions + line["other_deductions"]
            if line.get("parking_fee_deduction"):
                parking_fee_deduction = (
                    parking_fee_deduction + line["parking_fee_deduction"]
                )

            if line.get("consolidated_benefits_support"):
                consolidated_benefits_support = (
                    consolidated_benefits_support
                    + line["consolidated_benefits_support"]
                )

            if line.get("kimisitu_sacco_contribution_deduction"):
                kimisitu_sacco_contribution_deduction = (
                    kimisitu_sacco_contribution_deduction
                    + line["kimisitu_sacco_contribution_deduction"]
                )

            if line.get("finnlemm_sacco_contribution_deduction"):
                finnlemm_sacco_contribution_deduction = (
                    finnlemm_sacco_contribution_deduction
                    + line["finnlemm_sacco_contribution_deduction"]
                )

        depart_dict = {
            "basic_salary": basic,
            "monthly_basic_salary": basic,
            "house_allowance": house_allowance,
            "other_benefits": other_benefits,
            "taxable_salary": taxable_salary,
            "tax_charged": tax_charge,
            "monthly_personal_relief": monthly_personal_relief,
            "transport_allowance": transport_allowance,
            "other_earnings": other_earnings,
            "paye": paye,
            "nssf": nssf,
            "medical_deduction": medical_deduction,
            "nhif": nhif,
            "biblio_sacco_contribution_deduction": sacco_contribution,
            "tax_allowance": tax_allowance,
            "welfare_contribution": welfare_contribution,
            "long_term_advance": long_term_advance,
            "advance_deduction": long_term_adv_ded,
            "school_fees": school_fees,
            "loan_amount": loan_amount,
            "advance": advance,
            "pension_contribution_deduction": pension_contribution,
            "pension": pension,
            "loan_deduction": absa_loan_deduction,
            "bonus": bonus,
            "mwito_sacco_contribution_deduction": mwito_contribution,
            "monthly_insurance_relief": monthly_insurance_relief,
            "overtime": overtime,
            "gratuity_total": gratuity_total,
            "gratuity": gratuity,
            "_insurance_premium-deduction": insurance_premium_deduction,
            "helb_deduction": helb_deduction,
            "test_rule": test_rule,
            "other_deductions": other_deductions,
            "parking_fee-deduction": parking_fee_deduction,
            "consolidated_benefits_support": consolidated_benefits_support,
            "kimisitu_sacco_contribution-deduction": kimisitu_sacco_contribution_deduction,
            "finnlemm_sacco_contribution-deduction": finnlemm_sacco_contribution_deduction,
            "total_earning": total_earnings,
            "total_deductions": total_deductions,
            "net_salary": net_salary,
        }

        # Depart Dynamic Data Fetch from common dictionary
        depart_total_dict = {}
        for i in header_rows:
            if i not in ["staff_no", "name"]:
                if i in depart_dict:
                    depart_total_dict[i] = depart_dict[i]
                else:
                    depart_total_dict[i] = 0

        return depart_total_dict

    # Dynamic Grand Total Logic
    def grand_total_logic(self, date_dicts, header_rows):
        total_basic = (
            total_house_allowance
        ) = (
            grand_net_salary
        ) = (
            total_monthly_insurance_relief
        ) = (
            total_other_earnings
        ) = (
            total_overtime
        ) = (
            total_tax_allowance
        ) = (
            grand_total_earnings
        ) = (
            total_pension
        ) = (
            total_pension_contribution
        ) = (
            total_paye
        ) = (
            total_nssf
        ) = (
            total_nhif
        ) = (
            total_insurance
        ) = (
            total_advance
        ) = (
            total_welfare_contribution
        ) = (
            total_absa_loan_deduction
        ) = (
            total_sacco_contribution
        ) = (
            total_mwito_contribution
        ) = (
            total_school_fees
        ) = (
            total_long_term_adv_ded
        ) = (
            grand_total_deductions
        ) = (
            total_loan_amount
        ) = (
            total_long_term_advance
        ) = (
            total_medical_deduction
        ) = (
            total_bonus
        ) = (
            total_transport_allowance
        ) = (
            total_other_benefits
        ) = (
            total_taxable_salary
        ) = total_tax_charge = total_monthly_personal_relief = 0.0
        sum_gratuity_total = (
            total_gratuity
        ) = (
            total_insurance_premium_deduction
        ) = (
            total_helb_deduction
        ) = (
            total_test_rule
        ) = (
            total_consolidated_benefits_support
        ) = (
            total_kimisitu_sacco_contribution_deduction
        ) = total_finnlemm_sacco_contribution_deduction = 0.0
        total_other_deductions = 0
        total_parking_fee_deduction = 0.0

        basic_total = []
        for records in date_dicts:
            if records.get("basic_salary"):
                basic_total.append(records.get("basic_salary"))
            if records.get("monthly_basic_salary"):
                basic_total.append(records.get("monthly_basic_salary"))

            if records.get("basic_salary"):
                total_basic = total_basic + records.get("basic_salary")
            if records.get("monthly_basic_salary"):
                total_basic = total_basic + records.get("monthly_basic_salary")

            total_house_allowance = (
                total_house_allowance + records.get("house_allowance")
                if records.get("house_allowance")
                else 0.0
            )
            total_other_earnings = (
                total_other_earnings + records.get("other_earnings")
                if records.get("other_earnings")
                else 0.0
            )
            total_overtime = (
                total_overtime + records.get("overtime")
                if records.get("overtime")
                else 0.0
            )
            total_tax_allowance = (
                total_tax_allowance + records.get("tax_allowance")
                if records.get("tax_allowance")
                else 0.0
            )
            grand_total_earnings = (
                grand_total_earnings + records.get("total_earning")
                if records.get("total_earning")
                else 0.0
            )
            total_pension = (
                total_pension + records.get("pension")
                if records.get("pension")
                else 0.0
            )
            total_pension_contribution = (
                total_pension_contribution
                + records.get("pension_contribution_deduction")
                if records.get("pension_contribution_deduction")
                else 0.0
            )
            total_paye = (
                total_paye + records.get("paye") if records.get("paye") else 0.0
            )
            total_nssf = (
                total_nssf + records.get("nssf") if records.get("nssf") else 0.0
            )
            total_nhif = (
                total_nhif + records.get("nhif") if records.get("nhif") else 0.0
            )
            total_insurance = (
                total_insurance + records.get("insurance")
                if records.get("insurance")
                else 0.0
            )
            total_monthly_insurance_relief = (
                total_monthly_insurance_relief + records.get("monthly_insurance_relief")
                if records.get("monthly_insurance_relief")
                else 0.0
            )
            total_advance = (
                total_advance + records.get("advance")
                if records.get("advance")
                else 0.0
            )
            total_welfare_contribution = (
                total_welfare_contribution + records.get("welfare_contribution")
                if records.get("welfare_contribution")
                else 0.0
            )
            total_absa_loan_deduction = (
                total_absa_loan_deduction + records.get("loan_deduction")
                if records.get("loan_deduction")
                else 0.0
            )
            total_sacco_contribution = (
                total_sacco_contribution
                + records.get("biblio_sacco_contribution_deduction")
                if records.get("biblio_sacco_contribution_deduction")
                else 0.0
            )
            total_mwito_contribution = (
                total_mwito_contribution
                + records.get("mwito_sacco_contribution_deduction")
                if records.get("mwito_sacco_contribution_deduction")
                else 0.0
            )
            total_school_fees = (
                total_school_fees + records.get("school_fees")
                if records.get("school_fees")
                else 0.0
            )
            total_long_term_adv_ded = (
                total_long_term_adv_ded + records.get("advance_deduction")
                if records.get("advance_deduction")
                else 0.0
            )
            grand_net_salary = (
                grand_net_salary + records.get("net_salary")
                if records.get("net_salary")
                else 0.0
            )
            grand_total_deductions = (
                grand_total_deductions + records.get("total_deductions")
                if records.get("total_deductions")
                else 0.0
            )
            total_monthly_personal_relief = (
                total_monthly_personal_relief + records.get("monthly_personal_relief")
                if records.get("monthly_personal_relief")
                else 0.0
            )
            total_taxable_salary = (
                total_taxable_salary + records.get("taxable_salary")
                if records.get("taxable_salary")
                else 0.0
            )
            total_tax_charge = (
                total_tax_charge + records.get("tax_charged")
                if records.get("tax_charged")
                else 0.0
            )
            total_transport_allowance = (
                total_transport_allowance + records.get("transport_allowance")
                if records.get("transport_allowance")
                else 0.0
            )
            total_bonus = (
                total_bonus + records.get("bonus") if records.get("bonus") else 0.0
            )
            total_other_benefits = (
                total_other_benefits + records.get("other_benefits")
                if records.get("other_benefits")
                else 0.0
            )
            total_loan_amount = (
                total_loan_amount + records.get("loan_amount")
                if records.get("loan_amount")
                else 0.0
            )
            total_medical_deduction = (
                total_medical_deduction + records.get("medical_deduction")
                if records.get("medical_deduction")
                else 0.0
            )
            total_long_term_advance = (
                total_long_term_advance + records.get("long_term_advance")
                if records.get("long_term_advance")
                else 0.0
            )
            sum_gratuity_total = (
                sum_gratuity_total + records.get("gratuity_total")
                if records.get("gratuity_total")
                else 0.0
            )
            total_gratuity = (
                total_gratuity + records.get("gratuity")
                if records.get("gratuity")
                else 0.0
            )
            total_insurance_premium_deduction = (
                total_insurance_premium_deduction
                + records.get("_insurance_premium-deduction")
                if records.get("_insurance_premium-deduction")
                else 0.0
            )
            total_helb_deduction = (
                total_helb_deduction + records.get("helb_deduction")
                if records.get("helb_deduction")
                else 0.0
            )

            total_test_rule = (
                total_test_rule + records.get("test_rule")
                if records.get("test_rule")
                else 0.0
            )
            total_consolidated_benefits_support = (
                total_consolidated_benefits_support
                + records.get("consolidated_benefits_support")
                if records.get("consolidated_benefits_support")
                else 0.0
            )
            total_kimisitu_sacco_contribution_deduction = (
                total_kimisitu_sacco_contribution_deduction
                + records.get("kimisitu_sacco_contribution-deduction")
                if records.get("kimisitu_sacco_contribution-deduction")
                else 0.0
            )
            total_finnlemm_sacco_contribution_deduction = (
                total_finnlemm_sacco_contribution_deduction
                + records.get("finnlemm_sacco_contribution-deduction")
                if records.get("finnlemm_sacco_contribution-deduction")
                else 0.0
            )
            total_other_deductions = (
                total_other_deductions + records.get("other_deductions")
                if records.get("other_deductions")
                else 0.0
            )
            total_parking_fee_deduction = total_parking_fee_deduction + records.get(
                "parking_fee-deduction"
            )

        depart_dict = {
            "basic_salary": total_basic,
            "monthly_basic_salary": total_basic,
            "house_allowance": total_house_allowance,
            "other_benefits": total_other_benefits,
            "taxable_salary": total_taxable_salary,
            "tax_charged": total_tax_charge,
            "monthly_personal_relief": total_monthly_personal_relief,
            "transport_allowance": total_transport_allowance,
            "other_earnings": total_other_earnings,
            "paye": total_paye,
            "nssf": total_nssf,
            "medical_deduction": total_medical_deduction,
            "nhif": total_nhif,
            "biblio_sacco_contribution_deduction": total_sacco_contribution,
            "tax_allowance": total_tax_allowance,
            "welfare_contribution": total_welfare_contribution,
            "long_term_advance": total_long_term_advance,
            "advance_deduction": total_long_term_adv_ded,
            "school_fees": total_school_fees,
            "loan_amount": total_loan_amount,
            "advance": total_advance,
            "pension_contribution_deduction": total_pension_contribution,
            "pension": total_pension,
            "loan_deduction": total_absa_loan_deduction,
            "bonus": total_bonus,
            "mwito_sacco_contribution_deduction": total_mwito_contribution,
            "monthly_insurance_relief": total_monthly_insurance_relief,
            "overtime": total_overtime,
            "gratuity_total": sum_gratuity_total,
            "gratuity": total_gratuity,
            "_insurance_premium-deduction": total_insurance_premium_deduction,
            "helb_deduction": total_helb_deduction,
            "test_rule": total_test_rule,
            "consolidated_benefits_support": total_consolidated_benefits_support,
            "kimisitu_sacco_contribution-deduction": total_kimisitu_sacco_contribution_deduction,
            "finnlemm_sacco_contribution-deduction": total_finnlemm_sacco_contribution_deduction,
            "parking_fee-deduction": total_parking_fee_deduction,
            "other_deductions": total_other_deductions,
            "total_earning": grand_total_earnings,
            "total_deductions": grand_total_deductions,
            "net_salary": grand_net_salary,
        }

        # Grand Total Depart Dynamic Data Fetch from common dictionary
        grand_total_dict = {}
        for i in header_rows:
            if i not in ["staff_no", "name"]:
                if i in depart_dict:
                    grand_total_dict[i] = depart_dict[i]
                else:
                    if i in date_dicts:
                        grand_total_dict[i] = date_dicts[i]
                    else:
                        grand_total_dict[i] = 0
        return grand_total_dict

    # Dynamic Column and content fetch data
    def generate_xlsx_report(self, workbook, data, payslip):
        format1 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "bold": True, "font_name": "Arial"}
        )
        format2 = workbook.add_format(
            {"font_size": 10, "align": "vcenter", "font_name": "Arial"}
        )
        sheet = workbook.add_worksheet("ms_report")

        # Header Row Sets
        for j in range(0, len(data["field_col"])):
            each_col = data["field_col"][j].replace("_", " ")
            header_col = each_col.title()
            if header_col == "Total Earning":
                header_col = "Gross Salary"
            sheet.write(0, j, header_col, format1)
            j = j + 1

        # Dynamic Header Value fetch
        struc_id = data["salary_structure_id"]
        trcs_rec = (
            self.env["hr.payroll.structure"].sudo().search([("id", "=", struc_id)])
        )
        fields_col = []
        first_col = ["Staff No", "Name"]
        col_header = []
        for i in trcs_rec.rule_ids:
            vals = {"name": i.name, "code": i.code, "category": i.category_id.name}
            fields_col.append(vals)
            col_header.append(i.name)

        col_header.remove("Gross")
        col_header.remove("Net Salary")
        fields_col = []
        [fields_col.append(x) for x in col_header if x not in fields_col]

        total_list = ["Total Earning", "Total Deductions", "Net Salary"]
        conn_list = first_col + fields_col + total_list

        dict_vals = {}
        for i in range(0, len(conn_list)):
            each_col = conn_list[i].replace(" ", "_")
            if conn_list[i] == "Pension contribution-deduction":
                test = conn_list[i].replace(" ", "_")
                each_col = test.replace("-", "_")
            if conn_list[i] == "Insurance premium-deduction":
                test = conn_list[i].replace(" ", "_")
                each_col = test.replace("-", "_")
            key_col = each_col.lower()
            dict_vals[key_col] = 0

        header_rows = list(dict_vals.keys())
        result = data["form"]["payslip_data"]
        i = 0
        dates_dict = []
        for rec in result:
            i = i + 1
            sheet.write(i, 0, "DEPARTMENT", format1)
            sheet.write(i, 1, rec["department_name"], format1)
            department_no_employees = len(rec["line_ids"]) or 0
            for line in rec["line_ids"]:
                i = i + 1
                for k in range(0, len(line)):
                    sheet.write(i, k, list(line.values())[k], format2)
            i = i + 1
            string_1 = "DEPARTMENT " + "- " + rec["department_name"] + " -" + " TOTAL"
            sheet.write(i, 0, string_1, format1)

            # Department Value Fetch
            department_total = self.department_total_logic(rec["line_ids"], header_rows)

            dates_dict.append(department_total)

            l = 2
            for k in range(0, len(department_total)):
                sheet.write(i, l, list(department_total.values())[k], format1)
                l = l + 1
            i = i + 1
            string_2 = (
                "TOTAL NO OF EMPLOYEES IN DEPARTMENT "
                + "- "
                + rec["department_name"]
                + " - "
                + str(department_no_employees)
            )
            sheet.write(i, 0, string_2, format1)

        i = i + 1
        sheet.write(i, 0, "GRAND TOTAL", format1)

        # Grand total Value Fetch
        grand_total_value = self.grand_total_logic(dates_dict, header_rows)
        l = 2
        for k in range(0, len(grand_total_value)):
            sheet.write(i, l, list(grand_total_value.values())[k], format1)
            l = l + 1
