package net.fabricmc.example;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricEntityTypeBuilder;
import net.minecraft.client.render.entity.SpiderEntityRenderer;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.entity.*;
import net.minecraft.entity.attribute.DefaultAttributeContainer;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.boss.BossBar;
import net.minecraft.entity.boss.ServerBossBar;
import net.minecraft.entity.mob.CaveSpiderEntity;
import net.minecraft.entity.mob.SpiderEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroups;
import net.minecraft.item.SpawnEggItem;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import net.minecraft.world.World;

public class ExampleMod implements ModInitializer, ClientModInitializer {
    public static final String MOD_ID = "spidermod";

    public static final EntityType<GiantSpiderBoss> GIANT_SPIDER = Registry.register(
            Registries.ENTITY_TYPE, new Identifier(MOD_ID, "giant_spider"),
            FabricEntityTypeBuilder.create(SpawnGroup.MONSTER, GiantSpiderBoss::new)
                    .dimensions(EntityDimensions.fixed(7.0f, 4.5f)).build()
    );

    public static final Item SPIDER_BOSS_SPAWN_EGG = Registry.register(
            Registries.ITEM, new Identifier(MOD_ID, "spider_boss_spawn_egg"),
            new SpawnEggItem(GIANT_SPIDER, 0x342D27, 0xFF0000, new Item.Settings())
    );

    @Override
    public void onInitialize() {
        FabricDefaultAttributeRegistry.register(GIANT_SPIDER, GiantSpiderBoss.createAttributes());
        ItemGroupEvents.modifyEntriesEvent(ItemGroups.SPAWN_EGGS).register(content -> {
            content.add(SPIDER_BOSS_SPAWN_EGG);
        });
    }

    @Override
    public void onInitializeClient() {
        EntityRendererRegistry.register(GIANT_SPIDER, (context) -> 
            new SpiderEntityRenderer(context) {
                @Override
                protected void setupTransforms(SpiderEntity spider, MatrixStack matrices, float animProg, float yaw, float delta) {
                    super.setupTransforms(spider, matrices, animProg, yaw, delta);
                    matrices.scale(5.0F, 5.0F, 5.0F); 
                }
            }
        );
    }

    public static class GiantSpiderBoss extends SpiderEntity {
        // Заменено: "Король Пауков" -> "Spider King"
        private final ServerBossBar bossBar = new ServerBossBar(
                Text.literal("Spider King"), BossBar.Color.RED, BossBar.Style.NOTCHED_10);

        public GiantSpiderBoss(EntityType<? extends SpiderEntity> type, World world) {
            super(type, world);
            this.bossBar.setDarkenSky(true);
        }

        public static DefaultAttributeContainer.Builder createAttributes() {
            return SpiderEntity.createSpiderAttributes()
                    .add(EntityAttributes.GENERIC_MAX_HEALTH, 200.0)
                    .add(EntityAttributes.GENERIC_ATTACK_DAMAGE, 4.0)
                    .add(EntityAttributes.GENERIC_ARMOR, 15.0)
                    .add(EntityAttributes.GENERIC_KNOCKBACK_RESISTANCE, 1.0);
        }

        @Override
        public void mobTick() {
            super.mobTick();
            this.bossBar.setPercent(this.getHealth() / this.getMaxHealth());
            if (!this.getWorld().isClient && this.getHealth() < 60.0f && this.age % 100 == 0) {
                for (int i = 0; i < 2; i++) {
                    CaveSpiderEntity minion = EntityType.CAVE_SPIDER.create(this.getWorld());
                    if (minion != null) {
                        minion.refreshPositionAndAngles(this.getX() + random.nextGaussian(), this.getY(), this.getZ() + random.nextGaussian(), 0, 0);
                        this.getWorld().spawnEntity(minion);
                    }
                }
            }
        }

        @Override
        public void onStartedTrackingBy(ServerPlayerEntity player) {
            super.onStartedTrackingBy(player);
            this.bossBar.addPlayer(player);
        }

        @Override
        public void onStoppedTrackingBy(ServerPlayerEntity player) {
            super.onStoppedTrackingBy(player);
            this.bossBar.removePlayer(player);
        }
    }
}
