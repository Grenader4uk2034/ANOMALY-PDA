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

tasks.register("verifyBundledAssets") {
    dependsOn("copyWebAssets", "copyReferenceData")
    doLast {
        val webRoot = layout.buildDirectory.dir("generated/webAssets/www").get().asFile
        val requiredFiles = listOf(
            "index.html",
            "app.js",
            "mobile.js",
            "data/reference/stashes_and_poi.json"
        )
        val missing = requiredFiles.filterNot { webRoot.resolve(it).isFile }
        if (missing.isNotEmpty()) {
            throw GradleException("Не найдены обязательные ресурсы APK: ${missing.joinToString()}")
        }
        val mapsDir = webRoot.resolve("maps")
        val mapCount = mapsDir.listFiles()?.count { it.isFile && it.extension.equals("png", true) } ?: 0
        if (mapCount == 0) {
            throw GradleException("В APK не попали PNG-карты: ${mapsDir.absolutePath}")
        }
        logger.lifecycle("ANOMALY-PDA assets OK: ${mapCount} карт, встроенный справочник найден")
    }
}

tasks.named("preBuild") {
    dependsOn("verifyBundledAssets")
}
