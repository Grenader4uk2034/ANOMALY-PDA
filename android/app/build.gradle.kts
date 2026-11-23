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

    exclude(
        "**/*.bak",
        "**/*.bak_*",
        "**/*.before_*"
    )

    doFirst {
        val generatedWebRoot = layout.buildDirectory.dir("generated/webAssets/www").get().asFile
        generatedWebRoot.walkTopDown()
            .filter {
                it.isFile && (
                    it.name.endsWith(".bak") ||
                    it.name.contains(".bak_") ||
                    it.name.contains(".before_")
                )
            }
            .forEach { it.delete() }
    }
}

tasks.register<Copy>("copyReferenceData") {
    from(rootProject.projectDir.parentFile.resolve("data/reference"))
    into(layout.buildDirectory.dir("generated/webAssets/www/data/reference"))
}

tasks.register<Copy>("copyFullEntityData") {
    from(rootProject.projectDir.parentFile.resolve("data/processed/all_entities.json"))
    into(layout.buildDirectory.dir("generated/webAssets/www/data"))
}

tasks.register<Copy>("copyGlobalMapAssets") {
    from(rootProject.projectDir.parentFile.resolve("research/global-map/build"))
    into(layout.buildDirectory.dir("generated/webAssets/www/global-map"))
}

tasks.register("verifyBundledAssets") {
    dependsOn("copyWebAssets", "copyReferenceData", "copyFullEntityData", "copyGlobalMapAssets")
    doLast {
        val webRoot = layout.buildDirectory.dir("generated/webAssets/www").get().asFile
        val requiredFiles = listOf(
            "index.html",
            "app.js",
            "mobile.js",
            "global-map.html",
            "global-map.js",
            "data/reference/stashes_and_poi.json",
            "data/all_entities.json",
            "global-map/map_manifest.json",
            "global-map/global_map.png"
        )
        val missing = requiredFiles.filterNot { webRoot.resolve(it).isFile }
        if (missing.isNotEmpty()) {
            throw GradleException("Не найдены обязательные ресурсы APK: ${missing.joinToString()}")
        }

        val manifestFile = webRoot.resolve("global-map/map_manifest.json")
        val manifest = groovy.json.JsonSlurper().parse(manifestFile) as Map<*, *>
        val levels = manifest["levels"] as? List<*> ?: emptyList<Any>()
        if (levels.size != 24) {
            throw GradleException("Ожидалось 24 текстуры поверхностных локаций, найдено: ${levels.size}")
        }
        val missingTiles = levels.mapNotNull { entry ->
            val texture = (entry as? Map<*, *>)?.get("texture") as? String
            if (texture == null || !webRoot.resolve("global-map/$texture").isFile) texture else null
        }
        if (missingTiles.isNotEmpty()) {
            throw GradleException("Не найдены текстуры глобальной карты: ${missingTiles.joinToString()}")
        }

        val mapsDir = webRoot.resolve("maps")
        val mapCount = mapsDir.listFiles()?.count { it.isFile && it.extension.equals("png", true) } ?: 0
        if (mapCount == 0) {
            throw GradleException("В APK не попали PNG-карты: ${mapsDir.absolutePath}")
        }
        logger.lifecycle("ANOMALY-PDA assets OK: ${mapCount} локальных карт, глобальная карта + ${levels.size} текстур, встроенный справочник найден")
    }
}

tasks.named("preBuild") {
    dependsOn("verifyBundledAssets")
}
