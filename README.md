# Django Base Project

- For developoment environment:

  - Setup .env as following:

    - For virtual environment

      ```
      DEBUG=1
      ALLOWED_HOSTS=*
      SECRET_KEY=foo
      ENVIRONMENT_TYPE=development

      DB_ENGINE=django.db.backends.postgresql
      DB_NAME=django_base
      DB_USER=postgres
      DB_PASSWORD=postgres
      DB_HOST=localhost
      DB_PORT=5432

      EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
      EMAIL_HOST=smtp.gmail.com
      EMAIL_USE_TLS=True
      EMAIL_PORT=587
      EMAIL_HOST_USER=youremail@gmail.com
      EMAIL_HOST_PASSWORD=yourpassword
      ```

    - For docker

      ```
      DEBUG=1
      ALLOWED_HOSTS=*
      SECRET_KEY=foo
      ENVIRONMENT_TYPE=development

      DB_ENGINE=django.db.backends.postgresql
      DB_NAME=django_base
      DB_USER=postgres
      DB_PASSWORD=postgres
      DB_HOST=db
      DB_PORT=5432

      POSTGRES_USER=postgres
      POSTGRES_PASSWORD=postgres
      POSTGRES_DB=django_base

      EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
      EMAIL_HOST=smtp.gmail.com
      EMAIL_USE_TLS=True
      EMAIL_PORT=587
      EMAIL_HOST_USER=youremail@gmail.com
      EMAIL_HOST_PASSWORD=yourpassword
      ```

- Management Commands

  ```
      python manage.py create_menus
      python manage.py create_privilege
  ```
