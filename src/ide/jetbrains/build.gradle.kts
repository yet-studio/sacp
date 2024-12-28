plugins {
    id("java")
    id("org.jetbrains.intellij") version "1.16.1"
    id("org.jetbrains.kotlin.jvm") version "1.9.21"
}

group = "com.sacp"
version = "0.1.0"

repositories {
    mavenCentral()
}

dependencies {
    implementation("org.eclipse.lsp4j:org.eclipse.lsp4j:0.21.1")
    testImplementation("org.junit.jupiter:junit-jupiter:5.9.2")
}

intellij {
    version.set("2023.3")
    type.set("IC") // IntelliJ IDEA Community Edition
    plugins.set(listOf("com.intellij.java", "PythonCore:233.13135.103"))
}

tasks {
    withType<JavaCompile> {
        sourceCompatibility = "17"
        targetCompatibility = "17"
    }

    withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile> {
        kotlinOptions.jvmTarget = "17"
    }

    patchPluginXml {
        sinceBuild.set("233")
        untilBuild.set("241.*")
    }

    signPlugin {
        certificateChain.set(System.getenv("CERTIFICATE_CHAIN"))
        privateKey.set(System.getenv("PRIVATE_KEY"))
        password.set(System.getenv("PRIVATE_KEY_PASSWORD"))
    }

    publishPlugin {
        token.set(System.getenv("PUBLISH_TOKEN"))
    }
}
