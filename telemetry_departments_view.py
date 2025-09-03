from app.extensions import db
from app.lib.core.api.api_logger import ApiLogger
from app.lib.models.models import AppDepartment, KpiDepartment
from app.views.api_view import ApiView


class TelemetryDepartmentsView(ApiView):
    def get_action(self):
        request_data = self.get_request_data()
        department_id = request_data.get('department_id')
        show_active = request_data.get('active')

        if department_id is not None:
            if not str(department_id).isdigit():
                self.add_error('Department ID must be an integer.')
                return self.response

            department = KpiDepartment.query.get(department_id)
            # print(vars(department))
            if department is None:
                self.add_error('Data not found.')
                return self.response

            else:
                response_data = {'department': department.to_dict()}
        else:
            if show_active is not None:
                departments = self.get_all_departments(is_active=show_active)
            else:
                departments = self.get_all_departments()
            
            response_data = {'departments': departments}

        self.set_success_data(response_data)
        return self.response

    def post_action(self):
        """Synchronize all fields from App_Department to Kpi_Department."""

        try:
            app_departments = AppDepartment.query.all()
            kpi_departments = KpiDepartment.query.all()
            kpi_departments_dict = {dept.department_id: dept for dept in kpi_departments} if kpi_departments else {}

            for app_dept in app_departments:
                kpi_dept = kpi_departments_dict.get(app_dept.department_id)
                if kpi_dept:
                    kpi_dept.department_id = app_dept.department_id
                    kpi_dept.department_name = app_dept.department_name
                    kpi_dept.parent_department_id = app_dept.parent_department_id
                    kpi_dept.department_code = app_dept.department_code
                    kpi_dept.display_name = app_dept.department_display_name
                    kpi_dept.description = app_dept.description
                    kpi_dept.is_active = app_dept.is_active
                    kpi_dept.manager_user_id = app_dept.manager_user_id
                    kpi_dept.updated_at = app_dept.updated_at
                else:
                    new_kpi_dept = KpiDepartment(
                        department_id=app_dept.department_id,
                        parent_department_id=app_dept.parent_department_id,
                        department_code=app_dept.department_code,
                        department_name=app_dept.department_name,
                        display_name=app_dept.department_display_name,
                        description=app_dept.description,
                        is_active=app_dept.is_active,
                        manager_user_id=app_dept.manager_user_id,
                        created_at=app_dept.created_at,
                        updated_at=app_dept.updated_at,
                    )
                    db.session.add(new_kpi_dept)

            db.session.commit()

            message = 'Departments synchronized successfully.'
            departments = self.get_all_departments()
            response_data = {'message': message, 'departments': departments}
            self.set_success_data(response_data)
            return self.response

        except Exception as e:
            db.session.rollback()
            ApiLogger.error(f'An error occurred: {str(e)}')
            self.add_error('internal_error')
            return self.response

    # @staticmethod
    # def get_all_departments():
    #     departments = [
    #         department.to_dict()
    #         for department in (
    #             KpiDepartment.query.order_by(KpiDepartment.is_active.desc(), KpiDepartment.department_name.asc()).all()
    #         )
    #     ]
    #     return departments

    @staticmethod
    def get_all_departments(is_active: bool = None):
        query = KpiDepartment.query

        if is_active is not None:
            query = query.filter(KpiDepartment.is_active == is_active)

        departments = [
            department.to_dict()
            for department in query.order_by(
                KpiDepartment.is_active.desc(),
                KpiDepartment.department_name.asc()
            ).all()
        ]
        
        return departments
