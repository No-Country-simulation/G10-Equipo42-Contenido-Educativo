# G10 - Equipo 42 | Plataforma de Contenido Educativo

Proyecto desarrollado como parte de la simulación laboral de **No Country** (Cohorte G10 - Equipo 42). El objetivo principal es construir una plataforma web interactiva y accesible orientada a la gestión, creación y consumo de contenido educativo de calidad.

---

## 📌 Tabla de Contenidos

- [Sobre el Proyecto](#-sobre-el-proyecto)
- [Objetivos](#-objetivos)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Convenciones de Trabajo](#-convenciones-de-trabajo)
  - [Ramas (Git Flow)](#ramas-git-flow)
  - [Mensajes de Commit](#mensajes-de-commit)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Equipo](#-equipo)

---

## 📖 Sobre el Proyecto

En un entorno digital en constante evolución, el acceso a recursos educativos interactivos, estructurados y colaborativos resulta fundamental. Este proyecto busca resolver los principales retos en la distribución y asimilación de conocimiento, conectando a creadores de contenido educativo y estudiantes a través de una experiencia moderna y enriquecedora.

---

## 🎯 Objetivos

- **Accesibilidad y usabilidad:** Diseñar una interfaz intuitiva con altos estándares de experiencia de usuario (UX/UI).
- **Gestión eficiente de contenido:** Facilitar la organización de recursos por módulos, categorías y niveles de dificultad.
- **Interactividad y seguimiento:** Permitir a los usuarios seguir su progreso y participar de forma activa en su proceso de aprendizaje.
- **Arquitectura escalable:** Establecer bases sólidas de código, tanto en frontend como en backend, siguiendo buenas prácticas de la industria.

---

## 📂 Estructura del Proyecto

```text
├── .agents/          # Habilidades y agentes de asistencia y automatización
├── _bmad/            # Configuración y módulos del framework BMAD
├── _bmad-output/     # Artefactos generados (planeación, arquitectura, requerimientos)
├── .gitignore        # Reglas de exclusión para Git
└── README.md         # Documentación principal del repositorio
```

> A medida que se avance en la implementación, se integrarán los directorios correspondientes al código fuente (`client/`, `server/`, etc.).

---

## 🛠️ Convenciones de Trabajo

### Ramas (Git Flow)

- `main`: Código estable y listo para producción.
- `develop`: Rama principal de integración y desarrollo.
- `feature/<nombre-tarea>`: Nuevas funcionalidades (ej. `feature/auth-login`).
- `fix/<nombre-error>`: Corrección de errores (ej. `fix/navbar-responsive`).
- `hotfix/<nombre-urgente>`: Parches directos sobre código productivo.

### Mensajes de Commit

Se recomienda utilizar la convención de [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nueva funcionalidad o característica.
- `fix:` Corrección de bugs o errores.
- `docs:` Cambios únicamente en documentación.
- `style:` Cambios de formato, estilos o espaciado (sin cambios en lógica).
- `refactor:` Refactorización de código sin modificar funcionalidad.
- `test:` Inclusión o actualización de pruebas.
- `chore:` Tareas rutinarias, configuración o mantenimiento de dependencias.

---

## 🚀 Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/No-Country-simulation/G10-Equipo42-Contenido-Educativo.git
   cd G10-Equipo42-Contenido-Educativo
   ```

2. **Crear rama de trabajo:**
   ```bash
   git checkout -b feature/nombre-de-tu-rama
   ```

3. **Configurar variables de entorno:**
   - Copiar el archivo `.env.example` a `.env` cuando esté disponible y configurar las credenciales necesarias.

---

## 👥 Equipo

Proyecto desarrollado por el **Equipo 42 (No Country - Cohorte G10)**.
