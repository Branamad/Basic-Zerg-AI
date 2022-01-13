import sc2
import random
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.effect_id import EffectId
from sc2.unit import Unit
from sc2.data import race_townhalls
class KingsSwarm(sc2.BotAI):
    def __init__(self):
        self.ITERATIONS_PER_MINUTE = 165
        self.MAX_WORKERS = 22

    async def on_step(self, iteration):
        # What to do every step
        self.iteration = iteration
        await self.distribute_workers()
        await self.build_workers()
        await self.spawn_overlords()
        await self.expand()
        await self.build_extractor()
        await self.build_offensive_buildings()
        await self.build_offensive_force()
        await self.attack()
        await self.inject_larva()
        await self.build_queens()

    async def build_workers(self):
        all_base = self.units(UnitTypeId.HATCHERY) + self.units(UnitTypeId.LAIR) + self.units(UnitTypeId.HIVE)
        if len(self.units(UnitTypeId.DRONE)) < (self.MAX_WORKERS * len(all_base)):
            for wormyboi in self.units(UnitTypeId.LARVA).ready.idle:
                if self.units(UnitTypeId.DRONE).amount < 22 and self.can_afford(UnitTypeId.DRONE):
                    await self.do(wormyboi(AbilityId.LARVATRAIN_DRONE))
                elif self.units(UnitTypeId.SPAWNINGPOOL).ready.amount >= 1 and self.can_afford(UnitTypeId.DRONE):
                        if self.units(UnitTypeId.DRONE).amount > self.units(UnitTypeId.ZERGLING).amount:
                            return
                        elif self.can_afford(UnitTypeId.DRONE):
                            await self.do(wormyboi(AbilityId.LARVATRAIN_DRONE))
              #  elif self.can_afford(UnitTypeId.DRONE):
               #     await self.do(wormyboi(AbilityId.LARVATRAIN_DRONE))

    async def spawn_overlords(self):
        if self.supply_left < 5 and not self.already_pending(UnitTypeId.OVERLORD):
            wormybois = self.units(UnitTypeId.LARVA).ready
            if wormybois.exists:
                if self.can_afford(UnitTypeId.OVERLORD):
                    await self.do(wormybois[0](AbilityId.LARVATRAIN_OVERLORD))

    async def expand(self):
        all_base = self.units(UnitTypeId.HATCHERY) + self.units(UnitTypeId.LAIR) + self.units(UnitTypeId.HIVE)
        if self.can_afford(UnitTypeId.HATCHERY):
            if len(all_base) < 3:
                await self.expand_now()

    async def build_extractor(self):
        for hatchers in self.units(UnitTypeId.HATCHERY).ready:
            vaspenes = self.state.vespene_geyser.closer_than(20, hatchers)
            for vaspene in vaspenes:
                if not self.can_afford(UnitTypeId.EXTRACTOR):
                    break
                drones = self.select_build_worker(vaspene.position)
                if drones is None:
                    break
                if not self.units(UnitTypeId.EXTRACTOR).closer_than(1.0, vaspene).exists and not self.already_pending(UnitTypeId.EXTRACTOR) and self.units(UnitTypeId.DRONE).amount > 15:
                    await self.do(drones.build(UnitTypeId.EXTRACTOR, vaspene))

    async def build_offensive_buildings(self):
        homebase = self.units(UnitTypeId.HATCHERY) + self.units(UnitTypeId.LAIR) + self.units(UnitTypeId.HIVE)
        if self.can_afford(UnitTypeId.SPAWNINGPOOL):
            if self.units(UnitTypeId.SPAWNINGPOOL).amount < 1:
                wigglyboi = self.select_build_worker(homebase[0].position)
                await self.build(UnitTypeId.SPAWNINGPOOL, near=homebase[0])

        if self.units(UnitTypeId.SPAWNINGPOOL).amount > 0 and self.can_afford(UnitTypeId.LAIR):
            if self.units(UnitTypeId.LAIR).amount < 1:
                await self.do(homebase[0](AbilityId.UPGRADETOLAIR_LAIR))

        if self.units(UnitTypeId.LAIR).amount > 0 and self.can_afford(UnitTypeId.HYDRALISKDEN):
            if self.units(UnitTypeId.HYDRALISKDEN).amount < 1:
                wigglyboi = self.select_build_worker(homebase[0].position)
                await self.build(UnitTypeId.HYDRALISKDEN, near=homebase[0])

    async def build_offensive_force(self):
        for wigglybois in self.units(UnitTypeId.LARVA).ready.idle:
            if self.can_afford(UnitTypeId.HYDRALISK) and self.supply_left > 0 and self.units(UnitTypeId.HYBRID).amount < (self.units(UnitTypeId.ZERGLING).amount/3):
                await self.do(wigglybois(AbilityId.LARVATRAIN_HYDRALISK))

            if self.can_afford(UnitTypeId.ZERGLING) and self.supply_left > 0 and self.units(UnitTypeId.SPAWNINGPOOL).ready.exists:
                await self.do(wigglybois(AbilityId.LARVATRAIN_ZERGLING))

    async def attack(self):
        # {UNIT: [n to fight, n to defend]
        aggressive_units = {UnitTypeId.ZERGLING: [20, 3],
                            UnitTypeId.HYDRALISK:[7, 3]}
        for UNIT in aggressive_units:
            if self.units(UNIT).amount > aggressive_units[UNIT][0] and self.units(UNIT).amount > aggressive_units[UNIT][1]:
                for z in self.units(UNIT).idle:
                    await self.do(z.attack(self.find_target(self.state)))

            elif self.units(UNIT).amount > aggressive_units[UNIT][1]:
                if len(self.known_enemy_units) > 2:
                    if self.known_enemy_units[0] is UnitTypeId.SCV:
                        return
                    else:
                        for z in self.units(UNIT).idle:
                            await self.do(z.attack(random.choice(self.known_enemy_units)))

    def find_target(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        elif len(self.known_enemy_structures) > 0:
            return self.enemy_start_locations[0]


       async def build_queens(self):
        all_bases = self.units(race_townhalls[Race.Zerg])
        if self.can_afford(UnitTypeId.QUEEN) and self.units(UnitTypeId.SPAWNINGPOOL).amount > 0:
            if self.units(UnitTypeId.QUEEN).amount < len(all_bases):
                await self.do(all_bases.random.train(UnitTypeId.QUEEN))

                #Build a queen if a base does not have one
                #How to cycle through all bases
                #How to determine if Queen is near

    async def inject_larva(self):
        all_bases = self.units(race_townhalls[Race.Zerg])
        all_queens = self.units(race_townhalls[Race.Zerg])
        if len(all_queens) > 0:
            for queen in self.units(UnitTypeId.QUEEN).idle:
                larva_time = await self.get_available_abilities(queen)
                if AbilityId.EFFECT_INJECTLARVA in larva_time:
                    await self.do(queen(AbilityId.EFFECT_INJECTLARVA, all_bases.first))

run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Zerg, KingsSwarm()),
    Computer(Race.Terran, Difficulty.Hard)
    ], realtime=True)

