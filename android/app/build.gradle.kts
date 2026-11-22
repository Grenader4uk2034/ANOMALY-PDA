plugins {
    id("com.android.application")
}

android {
    namespace = "ru.anomalypda"
    compileSdk = 35

    defaultConfig {
        applicationId = "ru.anomalypda"
        minSdk = 23
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    sourceSets["main"].assets.srcDir(layout.buildDirectory.dir("generated/webAssets"))
}

tasks.register<Copy>("copyWebAssets") {
    from(rootProject.projectDir.parentFile.resolve("web"))
    into(layout.buildDirectory.dir("generated/webAssets/www"))
}

tasks.register<Copy>("copyReferenceData") {
    from(rootProject.projectDir.parentFile.resolve("data/reference"))
    into(layout.buildDirectory.dir("generated/webAssets/www/data/reference"))
}

tasks.named("preBuild") {
    dependsOn("copyWebAssets", "copyReferenceData")
}
